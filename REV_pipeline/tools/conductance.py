#!/usr/bin/env python3
"""conductance.py  -  saturated single-phase Darcy conductance of the yarn network of a REV mesh (README, "Effective
conductance of the yarn network").
    .venv/bin/python -I conductance.py <case> [--axis y] [--kpar 1e-11] [--kperp 2.2e-12] [--variants a,b,...]
<case> needs system/blockMeshDict (uniform blocks stacked in z, as build_fields.py writes them), 0/eps and 0/yarnID.

Model: the yarn cells (eps <= 0.99) form a network of two-point Darcy fluxes, as in the solver: the coefficient of a face
between two yarn cells is the harmonic mean of their normal K components times area / distance; the gaps between the yarns
do not conduct (they are dry in the fabric-scale Richards model). Periodic in x and y (the REV box is one period), with a
mean pressure drop dp per period along the flow axis: p = p_periodic - dp*(number of periods crossed), so a face crossing
the periodic plane in the flow direction gets dp added to its pressure difference. One equation per yarn cell (no net flux),
one cell of each connected group of yarn cells pinned (the periodic part of p is defined up to a constant per group).
Output: K_eff = Q*L/(A*dp) per cross-section A of the fabric box (padding excluded), the weave factor
w_sat = K_eff/(phi_y*Kpar) with phi_y the yarn-cell fraction of the box, the share of the flux carried by faces between two
yarns along the flow axis, two crossing yarns, or one of each, and the check that the same flux crosses every plane.
K variants, built from the yarn axes (axis of each yarnID = its longer in-plane extent in cells):
  scalar           Kpar everywhere (job 3068)
  tensor           Kpar along the yarn axis, Kperp across (tensorA)
  tensor_crossKyy  tensor, the crossing yarns (axis not the flow axis) get Kpar along the flow axis
  tensor_yarnKzz   tensor, the yarns along the flow axis get Kpar across the thickness (z)
  scalar_yonly     scalar, crossing yarns impermeable
  tensor_yonly     tensor, crossing yarns impermeable"""
import argparse
import os
import re
import sys

import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import spsolve

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyseCut import field  # noqa: E402

VARIANTS = ["scalar", "tensor", "tensor_crossKyy", "tensor_yarnKzz", "scalar_yonly", "tensor_yonly"]


def grid(case):
    """cells per direction, cell size of the fabric box, number of padding layers below the box"""
    bm = open(os.path.join(case, "system/blockMeshDict")).read()
    blocks = re.findall(r"hex\s*\([\d\s]+\)\s*\((\d+)\s+(\d+)\s+(\d+)\)", bm)
    nzb = [int(b[2]) for b in blocks]
    N = (int(blocks[0][0]), int(blocks[0][1]), sum(nzb))
    v = np.array([[float(x) for x in t.split()] for t in
                  re.findall(r"\(\s*([-\d.e+]+\s+[-\d.e+]+\s+[-\d.e+]+)\s*\)", bm.split("vertices", 1)[1].split(");", 1)[0])])
    lo, hi = v.min(axis=0), v.max(axis=0)
    zl = np.unique(v[:, 2])
    zpad = nzb[0] if len(nzb) == 3 else 0
    nbox = nzb[1] if len(nzb) == 3 else nzb[0]
    zbox = (zl[1], zl[2]) if len(nzb) == 3 else (zl[0], zl[-1])
    d = np.array([(hi[0] - lo[0]) / N[0], (hi[1] - lo[1]) / N[1], (zbox[1] - zbox[0]) / nbox])
    return N, d, zpad, nbox


def yarn_axes(P, yid):
    """axis (0 = x, 1 = y) of each yarn cell: the longer in-plane extent, in cells, of its yarnID"""
    ax = np.full(P.shape, -1, dtype=int)
    for y in np.unique(yid[P]).astype(int):
        m = P & (yid == y)
        ni = np.count_nonzero(m.any(axis=(1, 2)))
        nj = np.count_nonzero(m.any(axis=(0, 2)))
        ax[m] = 0 if ni > nj else 1
    return ax


def k_normal(variant, ax, P, flow, kpar, kperp):
    """normal K component of every yarn cell for each face direction, shape P.shape + (3,)"""
    Kn = np.zeros(P.shape + (3,))
    along = P & (ax == flow)            # yarns along the flow axis
    cross = P & (ax != flow)            # crossing yarns
    if variant.startswith("scalar"):
        Kn[P] = kpar
    else:
        Kn[P] = kperp
        for a in (0, 1):
            Kn[P & (ax == a), a] = kpar     # along each yarn's own axis
        if variant == "tensor_crossKyy":
            Kn[cross, flow] = kpar
        if variant == "tensor_yarnKzz":
            Kn[along, 2] = kpar
    if variant.endswith("_yonly"):
        Kn[cross] = 0.0
    return Kn


def solve(P, ax, Kn, d, flow, dp=1.0):
    N = P.shape
    n = P.size
    I = np.arange(n).reshape(N, order="F")
    porous = P.ravel(order="F")
    pid = np.full(n, -1)
    pid[porous] = np.arange(porous.sum())
    fa, fb, fT, fwrap, fdir, fplane = [], [], [], [], [], []
    for a in range(3):
        if a < 2:                                       # x and y periodic
            J = np.roll(I, -1, axis=a)
            Pb = np.roll(P, -1, axis=a)
            Kb = np.roll(Kn[..., a], -1, axis=a)
            idx = np.indices(N)[a]
            wrap = idx == N[a] - 1
        else:                                           # z: no neighbour above the top layer
            J = np.roll(I, -1, axis=2)
            Pb = np.roll(P, -1, axis=2)
            Kb = np.roll(Kn[..., 2], -1, axis=2)
            Pb[..., -1] = False
            idx = np.indices(N)[2]
            wrap = np.zeros(N, dtype=bool)
        m = P & Pb
        ka, kb = Kn[..., a][m], Kb[m]
        with np.errstate(invalid="ignore", divide="ignore"):
            kh = np.where(ka + kb > 0, 2 * ka * kb / (ka + kb), 0.0)
        area = np.prod([d[b] for b in range(3) if b != a])
        T = kh * area / d[a]
        keep = T > 0
        fa.append(pid[I[m]][keep])
        fb.append(pid[J[m]][keep])
        fT.append(T[keep])
        fwrap.append((wrap[m] & (a == flow))[keep])
        fdir.append(np.full(keep.sum(), a))
        fplane.append(idx[m][keep])
    fa, fb, fT, fwrap = map(np.concatenate, (fa, fb, fT, fwrap))
    fdir, fplane = np.concatenate(fdir), np.concatenate(fplane)
    nu = porous.sum()
    L = sp.coo_matrix((np.concatenate([fT, fT, -fT, -fT]),
                       (np.concatenate([fa, fb, fa, fb]), np.concatenate([fa, fb, fb, fa]))), shape=(nu, nu)).tocsr()
    r = np.zeros(nu)
    np.add.at(r, fa[fwrap], -fT[fwrap] * dp)
    np.add.at(r, fb[fwrap], fT[fwrap] * dp)
    # one pinned cell per connected group of yarn cells (and every isolated cell)
    adj = sp.coo_matrix((np.ones(fa.size), (fa, fb)), shape=(nu, nu))
    ncomp, lab = connected_components(adj, directed=False)
    first = np.unique(lab, return_index=True)[1]
    keep = np.ones(nu, dtype=bool)
    keep[first] = False
    p = np.zeros(nu)
    p[keep] = spsolve(L[keep][:, keep].tocsc(), r[keep])
    # flux through each plane normal to the flow axis
    f = fdir == flow
    q = fT[f] * (p[fa[f]] - p[fb[f]] + dp * fwrap[f])
    Qp = np.bincount(fplane[f], weights=q, minlength=N[flow])
    # flux share by the families of the two cells of each face
    axu = ax.ravel(order="F")[porous]
    both_along = (axu[fa[f]] == flow) & (axu[fb[f]] == flow)
    both_cross = (axu[fa[f]] != flow) & (axu[fb[f]] != flow)
    share = [q[both_along].sum() / q.sum(), q[both_cross].sum() / q.sum(), q[~both_along & ~both_cross].sum() / q.sum()]
    spanning = np.unique(lab[fa[f][fwrap[f]]]).size
    return Qp, share, ncomp, spanning


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("--axis", default="y", choices=["x", "y"])
    ap.add_argument("--kpar", type=float, default=1e-11)
    ap.add_argument("--kperp", type=float, default=2.2e-12)
    ap.add_argument("--variants", default=",".join(VARIANTS))
    a = ap.parse_args()
    flow = "xy".index(a.axis)
    other = 1 - flow
    N, d, zpad, nbox = grid(a.case)
    n = int(np.prod(N))
    P = (field(os.path.join(a.case, "0/eps"), n) <= 0.99).reshape(N, order="F")
    yid = field(os.path.join(a.case, "0/yarnID"), n).reshape(N, order="F")
    ax = yarn_axes(P, yid)
    phi = P.sum() / (N[0] * N[1] * nbox)
    A = N[other] * d[other] * nbox * d[2]
    Lf = N[flow] * d[flow]
    print(f"{a.case}: mesh {N}, cell {d * 1e6} um, fabric box {nbox} layers above {zpad}; yarn cells {P.sum():,}, "
          f"phi_y {phi:.4f}; along the flow axis ({a.axis}) {np.count_nonzero(P & (ax == flow)):,}, crossing "
          f"{np.count_nonzero(P & (ax == other)):,}; Kpar {a.kpar:g}, Kperp {a.kperp:g}")
    print(f"  {'variant':16s} K_eff [m2]   w_sat   / scalar | flux share: along / crossing / mixed faces | "
          "plane flux spread | groups (spanning)")
    ref = None
    for v in a.variants.split(","):
        Kn = k_normal(v, ax, P, flow, a.kpar, a.kperp)
        Qp, share, ncomp, span = solve(P, ax, Kn, d, flow)
        Q = Qp.mean()
        Keff = Q * Lf / A                              # dp = 1 Pa per period
        w = Keff / (phi * a.kpar)
        if v == "scalar":
            ref = w
        print(f"  {v:16s} {Keff:.4e}  {w:.4f}  {w / ref if ref else float('nan'):.4f} | "
              f"{share[0]:.3f} / {share[1]:.3f} / {share[2]:.3f} | {np.abs(Qp - Q).max() / Q:.1e} | {ncomp} ({span})")


if __name__ == "__main__":
    main()
