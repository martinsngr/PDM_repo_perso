#!/usr/bin/env python3
"""zLayers.py <run> [time ...]  -  water through the thickness (S9): per write the highest z layer of the free cells at least 20 % and 50 % water (alpha > 0.5), the top of the water
connected to the bottom, and the water fraction of each z layer."""
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "study2c_nearSaturation"))
from analyseCut import field, rlist  # noqa: E402

run = sys.argv[1]
times = sys.argv[2:] or sorted((x for x in os.listdir(run) if re.fullmatch(r"[0-9.e+-]+", x) and x != "0" and os.path.isfile(os.path.join(run, x, "alpha.wetting"))), key=float)
C, _ = rlist(f"{run}/0/C", vec=True)
n = len(C)
F = field(f"{run}/0/eps", n) > 0.99
own, _ = rlist(f"{run}/constant/polyMesh/owner")
nei, _ = rlist(f"{run}/constant/polyMesh/neighbour")
own, nei = own[:len(nei)].astype(int), nei.astype(int)
ff = F[own] & F[nei]
fo, fn = own[ff], nei[ff]
iz = np.round((C[:, 2] - C[:, 2].min()) / 20e-6).astype(int)
nz = iz.max() + 1
zr = np.array([C[iz == k, 2][0] for k in range(nz)]) * 1e3
nfree = np.bincount(iz[F], minlength=nz)
print("  t[ms] | top connected z [mm] | layer >=20 % / >=50 % [mm] | water fraction per z layer, bottom to top")
for t in times:
    a = field(f"{run}/{t}/alpha.wetting", n)
    w = F & (a > 0.5)
    reach = w & (iz == 0)
    while True:
        e = w[fo] & w[fn] & (reach[fo] != reach[fn])
        if not e.any():
            break
        reach[fo[e]] = True
        reach[fn[e]] = True
    frac = np.bincount(iz[w], minlength=nz) / np.maximum(nfree, 1)
    k20, k50 = np.where(frac >= 0.2)[0], np.where(frac >= 0.5)[0]
    print(f"  {float(t)*1e3:5.2f} | {C[reach, 2].max()*1e3 if reach.any() else float('nan'):6.3f} | {zr[k20.max()] if k20.size else float('nan'):6.3f} / {zr[k50.max()] if k50.size else float('nan'):6.3f} | " + " ".join(f"{f:.2f}" for f in frac))
