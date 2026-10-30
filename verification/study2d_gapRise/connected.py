#!/usr/bin/env python3
"""connected.py  -  gap water connected to the bath against isolated pockets (study2d_gapRise, 2026-10-30).
    ../../.venv/bin/python connected.py <run> [time ...]
Water = free cells with alpha > 0.5, fabric box or padding. Connected = reached from the free cells at the inlet through faces between water
cells. Per write: water cells connected / isolated, top of each, largest isolated pocket, and the rows at least 20 % and 50 % water (connected water
only). Yarn mean S and its change show whether the yarns feed the gaps."""
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "study2c_nearSaturation"))
from analyseCut import field, rlist  # noqa: E402


def main():
    run = sys.argv[1]
    times = sys.argv[2:] or sorted((x for x in os.listdir(run) if re.fullmatch(r"[0-9.e+-]+", x) and x != "0"
                                    and os.path.isfile(os.path.join(run, x, "alpha.wetting"))), key=float)
    C, _ = rlist(f"{run}/0/C", vec=True)
    n = len(C)
    P = field(f"{run}/0/eps", n) <= 0.99
    F = ~P
    own, _ = rlist(f"{run}/constant/polyMesh/owner")
    nei, _ = rlist(f"{run}/constant/polyMesh/neighbour")
    own, nei = own[:len(nei)].astype(int), nei.astype(int)
    v = open(f"{run}/system/blockMeshDict").read().split("vertices", 1)[1].split(");", 1)[0]
    zv = sorted({float(t.split()[2]) for t in re.findall(r"\(\s*([-\d.e+]+\s+[-\d.e+]+\s+[-\d.e+]+)\s*\)", v)})
    box = (C[:, 2] > zv[1]) & (C[:, 2] < zv[2])
    iy = np.round((C[:, 1] - C[:, 1].min()) / 20e-6).astype(int)
    ny = iy.max() + 1
    yr = np.array([C[iy == j, 1][0] for j in range(ny)]) * 1e3
    nfree = np.bincount(iy[F & box], minlength=ny)
    inlet = F & (iy == 0)
    ff = F[own] & F[nei]
    fo, fn = own[ff], nei[ff]
    print(f"{os.path.basename(run)}: water = free cells alpha > 0.5\n  t[ms] | connected cells, top [mm] | isolated cells, top [mm], largest pocket | row >=20 % / >=50 % connected [mm] | mean yarn S")
    for t in times:
        a = field(f"{run}/{t}/alpha.wetting", n)
        w = F & (a > 0.5)
        reach = inlet & w
        while True:
            e = w[fo] & w[fn] & (reach[fo] != reach[fn])
            if not e.any():
                break
            reach[fo[e]] = True
            reach[fn[e]] = True
        iso = w & ~reach
        # isolated pockets: labels by propagation over faces
        lab = np.full(n, -1)
        lab[iso] = np.where(iso)[0]
        while True:
            e = iso[fo] & iso[fn] & (lab[fo] != lab[fn])
            if not e.any():
                break
            m = np.minimum(lab[fo[e]], lab[fn[e]])
            np.minimum.at(lab, fo[e], m)
            np.minimum.at(lab, fn[e], m)
        big = np.bincount(lab[iso]).max() if iso.any() else 0
        frac = np.bincount(iy[reach & box], minlength=ny) / np.maximum(nfree, 1)
        k20, k50 = np.where(frac >= 0.2)[0], np.where(frac >= 0.5)[0]
        print(f"  {float(t)*1e3:5.2f} | {reach.sum():6d}, {C[reach,1].max()*1e3 if reach.any() else float('nan'):6.3f} | {iso.sum():6d}, "
              f"{C[iso,1].max()*1e3 if iso.any() else float('nan'):6.3f}, {big:5d} | {yr[k20.max()] if k20.size else float('nan'):6.3f} / "
              f"{yr[k50.max()] if k50.size else float('nan'):6.3f} | {a[P].mean():.4f}")


if __name__ == "__main__":
    main()
