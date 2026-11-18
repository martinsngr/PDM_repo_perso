"""Where are the alternating water-flux triplets on yarn/gap faces? One write of one case.

    ../../.venv/bin/python locate.py <label> <time folder> [height axis 0/1/2] [bath plane in m]

For the middle face of every alternating water triplet (scanREV.py, same threshold): the free cell's alpha, the porous
cell's S, |q| / p99, the height above the bath plane, the face normal; the same for all faces above the threshold (the
population it is drawn from); and how many alternating triplets chain into a 4-face zig-zag (odd-even signature).
"""
import os
import sys

import numpy as np

from scanREV import CASES, FLUX_REL, Mesh, first_field, read_internal, surface_setup


def main():
    label, td = sys.argv[1], sys.argv[2]
    hax = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    plane = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
    case = next(c for l, c, _ in CASES if l == label)
    mesh = Mesh(case)
    porous = first_field(case, "eps", mesh.nc) < 0.999
    pf, sgn, trip = surface_setup(mesh, porous)
    al = read_internal(os.path.join(case, td, "alpha.wetting"), mesh.nc)
    phi = read_internal(os.path.join(case, td, "phi"))[:mesh.ni]
    ap = read_internal(os.path.join(case, td, "alphaPhi0.wetting"))[:mesh.ni]
    q = sgn * ap[pf]
    p99 = np.percentile(np.abs(q), 99)
    thr = FLUX_REL * p99
    own, nei = mesh.own[pf], mesh.nei[pf]
    pc = np.where(porous[nei], nei, own)
    fcell = np.where(porous[nei], own, nei)
    a = np.abs(q)
    big3 = (a[trip] > thr).all(axis=1)
    qm, qc, qp = q[trip[:, 0]], q[trip[:, 1]], q[trip[:, 2]]
    alt = big3 & (qc * qm < 0) & (qc * qp < 0)
    mid = trip[alt, 1]
    # 4-face chains: two alternating triplets sharing two faces (m,c,p) and (c,p,pp)
    altset = {(int(m), int(c), int(p)) for m, c, p in trip[alt]}
    chains = sum((c, p, pp) in altset for (m, c, p) in altset for pp in
                 [x[2] for x in trip[alt] if x[0] == c and x[1] == p])
    h = (mesh.cc[pc, hax] - plane) * 1e3

    def describe(f, name):
        if len(f) == 0:
            print(f"{name}: none")
            return
        print(f"{name}: {len(f)} faces")
        print(f"  free-cell alpha  quartiles {np.percentile(al[fcell[f]], [0, 25, 50, 75, 100]).round(3)}")
        print(f"  porous S         quartiles {np.percentile(al[pc[f]], [0, 25, 50, 75, 100]).round(3)}")
        print(f"  |q| / p99        quartiles {np.percentile(a[f] / p99, [0, 25, 50, 75, 100]).round(4)}")
        print(f"  height above the plane (mm) quartiles {np.percentile(h[f], [0, 25, 50, 75, 100]).round(3)}")
        print(f"  water into the yarn: {(q[f] > 0).mean():.0%}")

    print(f"{label} t {td}: yarn/gap faces {len(pf)}, p99 |q_w| {p99:.3e} m3/s, threshold {thr:.3e}")
    describe(np.where(a > thr)[0], "faces above the threshold")
    describe(np.unique(mid), "middle faces of alternating triplets")
    print(f"alternating triplets {alt.sum()} of {big3.sum()}; 4-face zig-zag chains {chains}")
    inalt = np.unique(trip[alt].ravel())
    print(f"water exchange (m3/s): net into the yarns {q.sum():.3e}, gross {a.sum():.3e}; faces of alternating "
          f"triplets: gross {a[inalt].sum():.3e} ({a[inalt].sum() / a.sum():.1%} of the gross), net {q[inalt].sum():.3e}")


if __name__ == "__main__":
    main()
