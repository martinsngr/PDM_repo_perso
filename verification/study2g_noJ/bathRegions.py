#!/usr/bin/env python3
"""bathRegions.py  -  where the bath (inlet patch) feeds a study 2g case, per z layer of the fabric box (README, Results).
    .venv/bin/python -I bathRegions.py <case> [time ...]        (default: 0.5, 1, 2, 3 ms)
Needs <case>/0/C (compare3068.py writes it). Per write and per z layer of the free bath faces: water into the domain and
out of it through those faces (phi on the inlet patch, cell volumes per ms; the gross in and out, not only the net), the
number of faces with an outflow and the alpha of the cells behind them, and the first-row cells (the cells on the bath
faces) at alpha < 0.5. Then the same summed over the yarn band (z layers of the first-row yarn cells), the open space beside
the yarns and, inside it, the two outermost box layers next to the padding. With alpha fixedValue 1 on the inlet (N2) every
flux through the free faces is water; with J (R0) the faces of air-rich cells are closed."""
import os
import re
import sys

import numpy as np


def internal(path, n):
    body = open(path).read().split("internalField", 1)[1]
    m = re.match(r"\s*uniform\s+([^;]+);", body)
    if m:
        return np.full(n, float(m.group(1)))
    k = int(re.search(r"(\d+)\s*\(", body).group(1))
    return np.array(body.split("(", 1)[1].split(")", 1)[0].split()[:k], float)


def vectors(path):
    body = open(path).read().split("internalField", 1)[1]
    k = int(re.search(r"(\d+)\s*\(", body).group(1))
    return np.array([s.split() for s in re.findall(r"\(([^()]+)\)", body.split("(", 1)[1])[:k]], float)


def patch(path, name, k):
    bf = open(path).read().split("boundaryField", 1)[1]
    blk = re.search(r"\n    " + name + r"\n    \{(.*?)\n    \}", bf, re.S).group(1)
    m = re.search(r"\bvalue\s+nonuniform\s+List<scalar>\s*(\d+)\s*\((.*?)\)", blk, re.S)
    if m:
        return np.array(m.group(2).split(), float)
    m = re.search(r"\bvalue\s+uniform\s+([-\d.e+]+)", blk)
    if m:
        return np.full(k, float(m.group(1)))
    raise SystemExit(f"{path}: no value for patch {name}")


case = sys.argv[1]
times = sys.argv[2:] or ["0.0005", "0.001", "0.002", "0.003"]
own = np.array(open(f"{case}/constant/polyMesh/owner").read().split("(", 1)[1].split(")", 1)[0].split(), int)
m = re.search(r"\binlet\s*\{[^}]*nFaces\s+(\d+);\s*startFace\s+(\d+);", open(f"{case}/constant/polyMesh/boundary").read())
nF, sF = int(m.group(1)), int(m.group(2))
n = own.max() + 1
cell = own[sF:sF + nF]
C = vectors(f"{case}/0/C")
V = 1.0
zc = np.unique(np.round(C[:, 2], 9))
dz = np.median(np.diff(zc))
zl = np.round((C[cell, 2] - zc.min()) / dz).astype(int)          # z layer of each bath face (0 = lowest padding layer)
dx = np.median(np.diff(np.unique(np.round(C[:, 0], 9))))
dy = np.median(np.diff(np.unique(np.round(C[:, 1], 9))))
V = dx * dy * dz
free = internal(f"{case}/0/eps", n)[cell] > 0.99
band = (zl >= zl[~free].min()) & (zl <= zl[~free].max())        # z layers of the first-row yarn cells
outer = free & ((zl == zl[free].min()) | (zl == zl[free].max()))  # outermost box layers on the bath
s = 1e-3 / V
print(f"{os.path.basename(case.rstrip('/'))}: {nF} bath faces ({(~free).sum()} yarn, {free.sum()} free); z layers of the "
      f"free faces {zl[free].min()}-{zl[free].max()}, yarn band {zl[band].min()}-{zl[band].max()}; cell volumes per ms, "
      "+ = into the domain")
for t in times:
    phi = -patch(f"{case}/{t}/phi", "inlet", nF)                # + = into the domain
    a = internal(f"{case}/{t}/alpha.wetting", n)[cell]
    print(f"\n t = {float(t) * 1e3:g} ms\n  z layer | free faces | in | out (faces, alpha behind them min / median) | first-row cells a < 0.5")
    for k in np.unique(zl[free]):
        g = free & (zl == k)
        o = g & (phi < 0)
        print(f"  {k:7d} | {g.sum():10d} | {phi[g & (phi > 0)].sum() * s:7.0f} | {phi[o].sum() * s:7.0f} ({o.sum():3d}, "
              f"{a[o].min() if o.any() else np.nan:.2f} / {np.median(a[o]) if o.any() else np.nan:.2f}) | {(g & (a < 0.5)).sum()}")
    for name, g in (("yarn band", free & band), ("open space beside the yarns", free & ~band),
                    ("  of which the outermost layers", outer)):
        o = g & (phi < 0)
        print(f"  {name}: in {phi[g & (phi > 0)].sum() * s:.0f}, out {phi[o].sum() * s:.0f} ({o.sum()} faces), "
              f"first-row cells a < 0.5: {(g & (a < 0.5)).sum()} of {g.sum()}, mean alpha {a[g].mean():.3f}")
