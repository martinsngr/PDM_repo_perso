#!/usr/bin/env python3
"""inletFluxes.py  -  what crosses the bath (inlet patch) of a study 2g case, per write (README.md).
    .venv/bin/python -I inletFluxes.py <case> [<case> ...]
Per write: water (alphaPhi0.wetting) and air (phi - alphaPhi0.wetting) through the inlet, split into its porous (yarn)
and free (gap) faces, in cell volumes per ms, + = into the domain; free faces with an outflow (phi > 0 out of the
domain) and with air leaving; first-row free cells (the cells of the free inlet faces) with alpha > 0.5; min alpha of
those cells and of all cells. Faces and cells come from constant/polyMesh, porous cells from 0/eps."""
import os
import re
import sys

import numpy as np

V = 20e-6 ** 3


def internal(path, n=None):
    body = open(path).read().split("internalField", 1)[1]
    m = re.match(r"\s*uniform\s+([^;]+);", body)
    if m:
        return np.full(n, float(m.group(1)))
    k = int(re.search(r"(\d+)\s*\(", body).group(1))
    return np.array(body.split("(", 1)[1].split(")", 1)[0].split()[:k], float)


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


def times(case):
    return sorted((t for t in os.listdir(case) if re.fullmatch(r"[0-9.e+-]+", t) and t != "0"
                   and os.path.isfile(os.path.join(case, t, "phi"))), key=float)


for case in sys.argv[1:]:
    own = np.array(open(f"{case}/constant/polyMesh/owner").read().split("(", 1)[1].split(")", 1)[0].split(), int)
    bnd = open(f"{case}/constant/polyMesh/boundary").read()
    m = re.search(r"\binlet\s*\{[^}]*nFaces\s+(\d+);\s*startFace\s+(\d+);", bnd)
    nF, sF = int(m.group(1)), int(m.group(2))
    n = own.max() + 1
    cell = own[sF:sF + nF]
    eps = internal(f"{case}/0/eps", n)
    free = eps[cell] > 0.99
    print(f"\n{os.path.basename(case.rstrip('/'))}: inlet {nF} faces ({(~free).sum()} porous, {free.sum()} free); "
          "fluxes in cell volumes per ms, + = into the domain")
    print("  t[ms] | water porous / free | air porous / free | free faces out / air out | row-1 free water | "
          "min a row-1 free / all")
    for t in times(case):
        phi = -patch(f"{case}/{t}/phi", "inlet", nF)            # + = into the domain (outward normal)
        aphi = -patch(f"{case}/{t}/alphaPhi0.wetting", "inlet", nF)
        air = phi - aphi
        a = internal(f"{case}/{t}/alpha.wetting", n)
        s = 1e-3 / V
        print(f" {float(t)*1e3:6.3f} | {aphi[~free].sum()*s:8.1f} / {aphi[free].sum()*s:8.1f} | "
              f"{air[~free].sum()*s:7.2f} / {air[free].sum()*s:8.2f} | {(phi[free] < 0).sum():4d} / "
              f"{(air[free] < -1e-30).sum():4d} | {(a[cell[free]] > 0.5).sum():4d} | "
              f"{a[cell[free]].min():.3g} / {a.min():.3g}")
