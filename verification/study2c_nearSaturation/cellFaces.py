#!/usr/bin/env python3
"""cellFaces.py  -  the faces of one cell at one write: neighbour (porous/free, alpha), total flux phi, water flux
alphaPhi0.wetting and air flux (phi - water), all signed into the cell, as face velocities (flux / |Sf|), plus U and p
of the cell and its neighbours.
    ../../.venv/bin/python cellFaces.py <run> <time> <x> <y> <z>     (cell centre in mm; nearest cell)
Needs <run>/0/C (analyseCut.py writes it)."""
import os
import re
import sys

import numpy as np


def rlist(path, vec=False):
    txt = open(path).read()
    body = txt.split("internalField", 1)[1] if "internalField" in txt else txt.split("FoamFile", 1)[1].split("}", 1)[1]
    n = int(re.search(r"(\d+)\s*\(", body).group(1))
    data = body.split("(", 1)[1]
    if vec:
        return np.array([s.split() for s in re.findall(r"\(([^()]+)\)", data)[:n]], float)
    return np.array(data.split(")", 1)[0].split()[:n], float)


run, t = sys.argv[1], sys.argv[2]
xc = np.array([float(v) for v in sys.argv[3:6]]) * 1e-3
C = rlist(os.path.join(run, "0/C"), vec=True)
c = int(np.argmin(np.linalg.norm(C - xc, axis=1)))
nei = rlist(os.path.join(run, "constant/polyMesh/neighbour")).astype(int)
own = rlist(os.path.join(run, "constant/polyMesh/owner")).astype(int)[:len(nei)]
eps = rlist(os.path.join(run, "0/eps"))
a = rlist(os.path.join(run, t, "alpha.wetting"))
p = rlist(os.path.join(run, t, "p"))
U = rlist(os.path.join(run, t, "U"), vec=True)
phi = rlist(os.path.join(run, t, "phi"))[:len(nei)]
aphi = rlist(os.path.join(run, t, "alphaPhi0.wetting"))[:len(nei)]
A = 4e-10   # |Sf| of the faces of a 20 um cell (x and z faces 20.0 x 20.1 um, y faces 20.0 x 20.1: within 1 %)
kind = lambda j: "porous" if eps[j] <= 0.99 else "free  "
print(f"{run} t = {t}: cell {c} at {C[c]*1e3} mm, {kind(c)}, alpha {a[c]:.4f}, p {p[c]:.1f} Pa, "
      f"U {U[c]} (|U| {np.linalg.norm(U[c]):.3f} m/s)")
print(" face  dir  neighbour at [mm]            kind    alpha   p [Pa]  | into the cell [m/s]: total   water    air")
tot = wat = 0.0
for f in np.nonzero((own == c) | (nei == c))[0]:
    j = nei[f] if own[f] == c else own[f]
    s = -1.0 if own[f] == c else 1.0       # phi > 0 from owner to neighbour
    d = C[j] - C[c]
    ax = "xyz"[int(np.argmax(np.abs(d)))] + ("+" if d[np.argmax(np.abs(d))] > 0 else "-")
    q, w = s * phi[f], s * aphi[f]
    tot += q
    wat += w
    print(f"{f:7d}  {ax}   ({C[j][0]*1e3:6.3f}, {C[j][1]*1e3:6.3f}, {C[j][2]*1e3:6.3f})  {kind(j)} {a[j]:.4f} "
          f"{p[j]:8.1f} | {q/A:9.3f} {w/A:8.3f} {(q-w)/A:8.3f}")
print(f"sum into the cell: total {tot:.3e} m3/s, water {wat:.3e} m3/s (cell volume 8e-15 m3: d(alpha)/dt of the "
      f"cell ~ {wat/(8e-15):.3g} 1/s)")
