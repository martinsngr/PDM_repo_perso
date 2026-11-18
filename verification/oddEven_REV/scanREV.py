"""Odd-even (cell-to-cell alternation) scan of the REV outputs: saturation in the yarns, phase fluxes on yarn/gap faces.

    ../../.venv/bin/python scanREV.py [label ...]      (default: every case of CASES; method and cases in README.md)

Per write: zig-zag quadruples of S along x, y, z (porous cells and neighbours only; split along / across the cell's yarn),
strict local extrema of S among porous neighbours, alternating signs of the water and air fluxes along the yarn surface
(yarn/gap faces), counter-current yarn/gap faces. Prints one summary table and the largest zig-zags; writes
results/<label>.csv (one row per write). ASCII OpenFOAM files only.
"""
import csv
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RES = os.path.expanduser("~/PDM_results")
AMP = 1e-3        # S threshold of a zig-zag step and of a strict extremum
FLUX_REL = 1e-2   # flux threshold: this fraction of the 99th percentile of |q| on yarn/gap faces at the write
CASES = [  # label, case folder, saturation field
    ("eq_port", os.path.join(ROOT, "verification/eq_BC/port"), "alpha.wetting"),
    ("eq_ABC", os.path.join(ROOT, "verification/eq_BC/ABC"), "alpha.wetting"),
    ("3068", os.path.join(RES, "REV_midbath_run3068"), "alpha.wetting"),
    ("N2_full", os.path.join(RES, "study2g_N2_full"), "alpha.wetting"),
    ("N2c_full", os.path.join(RES, "study2g_N2c_full"), "alpha.wetting"),
    ("tensorA", os.path.join(RES, "REV_pipeline_tensorA"), "alpha.wetting"),
    ("tensorB", os.path.join(RES, "REV_pipeline_tensorB"), "alpha.wetting"),
    ("twillA", os.path.join(RES, "REV_pipeline_twillA"), "alpha.wetting"),
    ("horizB_t40", os.path.join(RES, "REV_pipeline_horizB_t40"), "alpha.wetting"),
    ("horizB_t85", os.path.join(RES, "REV_pipeline_horizB_t85"), "alpha.wetting"),
    ("anisoA", os.path.join(RES, "REV_pipeline_anisoA"), "Sb"),
]


# ---------------------------------------------------------------- readers
def _body(path):
    """count and body of the first counted list after the FoamFile header"""
    txt = open(path).read()
    txt = txt[txt.index("FoamFile"):]
    txt = txt[txt.index("}") + 1:]
    m = re.search(r"(\d+)\s*\(", txt)
    end = txt.index("\n)", m.end())
    return int(m.group(1)), txt[m.end():end]


def read_labels(path):
    n, body = _body(path)
    a = np.array(body.split(), dtype=np.int64)
    assert len(a) == n, path
    return a


def read_points(path):
    n, body = _body(path)
    a = np.array(body.replace("(", " ").replace(")", " ").split(), float).reshape(-1, 3)
    assert len(a) == n, path
    return a


def read_faces(path):
    n, body = _body(path)
    lines = body.split()
    a = np.array(body.replace("4(", " ").replace(")", " ").split(), dtype=np.int64)
    assert len(a) == 4 * n and sum(s.startswith("4(") for s in lines) == n, "hex meshes only: " + path
    return a.reshape(-1, 4)


def read_internal(path, n=None):
    """internalField of an ascii scalar field (vol or surface); uniform -> n copies"""
    txt = open(path).read()
    m = re.search(r"internalField\s+uniform\s+(\S+);", txt)
    if m:
        return np.full(n, float(m.group(1)))
    m = re.search(r"internalField\s+nonuniform\s+List<scalar>\s*(\d+)\s*\(", txt)
    a = np.array(txt[m.end():txt.index("\n)", m.end())].split(), dtype=float)
    assert len(a) == int(m.group(1)), path
    return a


def times(case):
    out = []
    for d in os.listdir(case):
        try:
            if float(d) > 0:
                out.append((float(d), d))
        except ValueError:
            pass
    return sorted(out)


# ---------------------------------------------------------------- mesh
class Mesh:
    def __init__(self, case):
        pm = os.path.join(case, "constant", "polyMesh")
        pts = read_points(os.path.join(pm, "points"))
        faces = read_faces(os.path.join(pm, "faces"))
        own = read_labels(os.path.join(pm, "owner"))
        nei = read_labels(os.path.join(pm, "neighbour"))
        ni = len(nei)
        nc = int(own.max()) + 1
        fc = pts[faces].mean(axis=1)
        cc = np.zeros((nc, 3))
        cnt = np.zeros(nc)
        np.add.at(cc, own, fc)
        np.add.at(cnt, own, 1)
        np.add.at(cc, nei, fc[:ni])
        np.add.at(cnt, nei, 1)
        assert (cnt == 6).all(), "hex cells only"
        cc /= 6
        o = own[:ni]
        d = cc[nei] - cc[o]
        ax = np.abs(d).argmax(axis=1)
        dirp = 2 * ax + (d[np.arange(ni), ax] < 0)  # direction index owner -> neighbour: 0 +x, 1 -x, 2 +y, ...
        nb = np.full((nc, 6), -1, dtype=np.int64)
        nb[o, dirp] = nei
        nb[nei, dirp ^ 1] = o
        assert (np.bincount(o * 6 + dirp, minlength=nc * 6) <= 1).all(), "two neighbours in one direction"
        self.nc, self.ni, self.own, self.nei, self.cc, self.nb, self.dirp = nc, ni, o, nei, cc, nb, dirp


def first_field(case, name, n):
    for _, d in [(0, "0")] + times(case):
        p = os.path.join(case, d, name)
        if os.path.exists(p):
            return read_internal(p, n)
    return None


def yarn_axis(mesh, yid, porous):
    """0 (x) or 1 (y) per porous cell: the longer in-plane extent of its yarn; -1 without yarnID"""
    ax = np.full(mesh.nc, -1)
    if yid is None:
        return ax
    for y in np.unique(yid[porous]):
        sel = porous & (yid == y)
        ext = np.ptp(mesh.cc[sel, :2], axis=0)
        ax[sel] = 0 if ext[0] > ext[1] else 1
    return ax


# ---------------------------------------------------------------- metrics
def zigzag(mesh, S, porous, yax):
    """per direction a: counts of zig-zag quadruples (m, c, p, pp) along a; along/across the yarn of c; largest one"""
    out, worst = {}, (0.0, None)
    for a in range(3):
        c = np.where(porous)[0]
        m, p = mesh.nb[c, 2 * a + 1], mesh.nb[c, 2 * a]
        ok = (m >= 0) & (p >= 0)
        c, m, p = c[ok], m[ok], p[ok]
        pp = mesh.nb[p, 2 * a]
        ok = (pp >= 0)
        c, m, p, pp = c[ok], m[ok], p[ok], pp[ok]
        ok = porous[m] & porous[p] & porous[pp]
        c, m, p, pp = c[ok], m[ok], p[ok], pp[ok]
        d1, d2, d3 = S[c] - S[m], S[p] - S[c], S[pp] - S[p]
        amp = np.minimum(np.minimum(np.abs(d1), np.abs(d2)), np.abs(d3))
        z = (d1 * d2 < 0) & (d2 * d3 < 0) & (amp > AMP)
        along = z & (yax[c] == a)
        out[a] = dict(eligible=len(c), zig=int(z.sum()), along=int(along.sum()), across=int((z & ~along).sum()))
        if z.any():
            k = np.argmax(np.where(z, amp, 0))
            if amp[k] > worst[0]:
                worst = (amp[k], dict(axis="xyz"[a], cells=(m[k], c[k], p[k], pp[k]),
                                      S=tuple(S[[m[k], c[k], p[k], pp[k]]]), centre=mesh.cc[c[k]]))
    return out, worst


def extrema(mesh, S, porous):
    lo = np.full(mesh.nc, np.inf)
    hi = np.full(mesh.nc, -np.inf)
    keep = porous[mesh.own] & porous[mesh.nei]
    o, n = mesh.own[keep], mesh.nei[keep]
    for a, b in ((o, n), (n, o)):
        np.minimum.at(lo, a, S[b])
        np.maximum.at(hi, a, S[b])
    amp = np.where(np.isfinite(lo), np.maximum(S - hi, lo - S), -np.inf)
    ext = porous & (amp > AMP)
    return int(ext.sum()), float(amp[ext].max()) if ext.any() else 0.0


def surface_setup(mesh, porous):
    """yarn/gap internal faces: sign into the yarn, and faceOf[porous cell, outward direction]"""
    pf = np.where(porous[mesh.own] != porous[mesh.nei])[0]
    pin_nei = porous[mesh.nei[pf]]                       # porous cell is the neighbour: owner->neighbour = into yarn
    sgn = np.where(pin_nei, 1.0, -1.0)
    pc = np.where(pin_nei, mesh.nei[pf], mesh.own[pf])
    out_dir = np.where(pin_nei, mesh.dirp[pf] ^ 1, mesh.dirp[pf])  # from the porous cell towards the free cell
    face_of = np.full((mesh.nc, 6), -1, dtype=np.int64)
    face_of[pc, out_dir] = np.arange(len(pf))
    # triplets (m, c, p) of surface faces on the same side, consecutive along a direction parallel to the face
    trip = []
    for n_dir in range(6):
        cs = pc[out_dir == n_dir]
        for t in range(3):
            if t == n_dir // 2:
                continue
            m, p = mesh.nb[cs, 2 * t + 1], mesh.nb[cs, 2 * t]
            ok = (m >= 0) & (p >= 0)
            c_, m, p = cs[ok], m[ok], p[ok]
            fm, fc_, fp = face_of[m, n_dir], face_of[c_, n_dir], face_of[p, n_dir]
            ok = (fm >= 0) & (fp >= 0)
            trip.append(np.stack([fm[ok], fc_[ok], fp[ok]], axis=1))
    trip = np.concatenate(trip) if trip else np.zeros((0, 3), dtype=np.int64)
    return pf, sgn, trip


def flux_alternation(q, trip):
    a = np.abs(q)
    thr = FLUX_REL * np.percentile(a, 99) if len(a) else 0.0
    qm, qc, qp = q[trip[:, 0]], q[trip[:, 1]], q[trip[:, 2]]
    big = (a[trip[:, 0]] > thr) & (a[trip[:, 1]] > thr) & (a[trip[:, 2]] > thr)
    alt = big & (qc * qm < 0) & (qc * qp < 0)
    return int(big.sum()), int(alt.sum()), thr


# ---------------------------------------------------------------- driver
def scan_case(label, case, field):
    mesh = Mesh(case)
    eps = first_field(case, "eps", mesh.nc)
    porous = np.ones(mesh.nc, bool) if eps is None else eps < 0.999
    yid = first_field(case, "yarnID", mesh.nc)
    yax = yarn_axis(mesh, yid, porous)
    pf, sgn, trip = surface_setup(mesh, porous)
    npor = int(porous.sum())
    rows, worst_all = [], (0.0, None, None)
    for tv, td in times(case):
        fS = os.path.join(case, td, field)
        if not os.path.exists(fS):
            continue
        S = read_internal(fS, mesh.nc)
        zz, worst = zigzag(mesh, S, porous, yax)
        next_, next_amp = extrema(mesh, S, porous)
        row = dict(t=tv, porous=npor, extrema=next_, extrema_amp=next_amp)
        for a in range(3):
            for k in ("eligible", "zig", "along", "across"):
                row[f"{'xyz'[a]}_{k}"] = zz[a][k]
        row["zig_total"] = sum(zz[a]["zig"] for a in range(3))
        row["zig_amp"] = worst[0]
        fphi = os.path.join(case, td, "phi")
        fap = os.path.join(case, td, "alphaPhi0.wetting")
        if len(pf) and os.path.exists(fphi) and os.path.exists(fap):
            phi = read_internal(fphi)[:mesh.ni]
            ap = read_internal(fap)[:mesh.ni]
            qw = sgn * ap[pf]
            qa = sgn * (phi[pf] - ap[pf])
            row["trip"] = len(trip)
            row["w_big"], row["w_alt"], tw = flux_alternation(qw, trip)
            row["a_big"], row["a_alt"], ta = flux_alternation(qa, trip)
            row["countercurrent"] = int(((qw > tw) & (qa < -ta)).sum())
            row["surface_faces"] = len(pf)
        rows.append(row)
        if worst[0] > worst_all[0]:
            worst_all = (worst[0], tv, worst[1])
        print(f"  {label} t {tv:g}: zig {row['zig_total']} ext {next_}"
              + (f" w_alt {row['w_alt']}/{row['w_big']} a_alt {row['a_alt']}/{row['a_big']}" if "trip" in row else ""),
              flush=True)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    keys = sorted({k for r in rows for k in r}, key=lambda k: (k != "t", k))
    with open(os.path.join(HERE, "results", f"{label}.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    return rows, worst_all, yid is not None


def main():
    sel = sys.argv[1:]
    summary = []
    for label, case, field in CASES:
        if sel and label not in sel:
            continue
        if not os.path.isdir(case):
            print(f"{label}: {case} missing, skipped")
            continue
        rows, worst, has_yid = scan_case(label, case, field)
        summary.append((label, rows, worst, has_yid))
    print("\n| Case | writes | t last | porous cells | zig-zags, max over writes (% porous) | along / across at that write "
          "| largest zig-zag step | strict extrema, max (% porous) | water alt. triplets, max share | air alt. triplets, "
          "max share | counter-current faces, max |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for label, rows, worst, has_yid in summary:
        if not rows:
            continue
        r = max(rows, key=lambda r: r["zig_total"])
        npor = r["porous"]
        al = sum(r[f"{c}_along"] for c in "xyz")
        ac = sum(r[f"{c}_across"] for c in "xyz")
        ext = max(x["extrema"] for x in rows)
        fl = [x for x in rows if "trip" in x]
        def share(k_alt, k_big):
            v = [(x[k_alt] / x[k_big], x[k_alt], x[k_big]) for x in fl if x[k_big]]
            return "—" if not v else "{:.2%} ({} of {})".format(*max(v))
        cc = "—" if not fl else str(max(x["countercurrent"] for x in fl))
        print(f"| {label} | {len(rows)} | {rows[-1]['t']:g} | {npor} | {r['zig_total']} ({r['zig_total'] / npor:.3%}) "
              f"| {al} / {ac}{'' if has_yid else ' (no yarnID)'} | {worst[0]:.2e} | {ext} ({ext / npor:.3%}) "
              f"| {share('w_alt', 'w_big')} | {share('a_alt', 'a_big')} | {cc} |")
    print("\nLargest zig-zag per case (time, axis, centre in mm, S of the four cells):")
    for label, rows, worst, _ in summary:
        if worst[2] is not None:
            w = worst[2]
            print(f"  {label}: t {worst[1]:g}, {w['axis']}, ({', '.join(f'{v * 1e3:.3f}' for v in w['centre'])}), "
                  f"S {', '.join(f'{v:.4f}' for v in w['S'])}")


if __name__ == "__main__":
    main()
