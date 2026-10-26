#!/usr/bin/env python3
"""Serial vs parallel 2D bench runs in <dir>/<case>/ (reconstructed): mirror asymmetry k <-> 23-k (lower vs
upper wall), max |dalpha| vs the serial run, gap meniscus (alpha 0.5) on the rows next to the lower and upper
wall and at mid-gap, wall front (alpha < 0.1) on the wall rows next to the gap, max |U|.
    python3 compare.py <dir> [case ...]   (default: serial par parfix parmid serialfix)"""
import os, re, sys
import numpy as np
SP = sys.argv[1]
CASES = sys.argv[2:] or ["serial", "par", "parfix", "parmid", "serialfix"]
NX, NZ = 100, 24

def read(case, t, name, vec=False):
    txt = open(os.path.join(SP, case, t, name)).read()
    body = txt.split("internalField", 1)[1]
    m = re.match(r"\s*uniform\s+([^;]+);", body)
    if m:
        v = np.array(m.group(1).strip("()").split(), float)
        return np.tile(v, (NX * NZ, 1)) if vec else np.full(NX * NZ, v[0])
    n = int(re.search(r">\s*(\d+)\s*\(", body).group(1))
    data = body.split("(", 1)[1]
    if vec:
        vals = re.findall(r"\(([^()]+)\)", data)[:n]
        a = np.array([v.split() for v in vals], float)
        return a.reshape(NZ, NX, 3)
    vals = data.split(")", 1)[0].split()[:n]
    return np.array(vals, float).reshape(NZ, NX)        # [k, i]

def meniscus(a, k):
    """x [mm] where alpha drops below 0.5 along row k (first crossing from the inlet)"""
    row = a[k]
    idx = np.where(row < 0.5)[0]
    if len(idx) == 0:
        return np.nan
    i = idx[0]
    if i == 0:
        return 0.0
    x0, x1 = (i - 0.5) * 0.02, (i + 0.5) * 0.02
    return x0 + (row[i - 1] - 0.5) / (row[i - 1] - row[i]) * (x1 - x0)

print(f"{'t [ms]':>7} {'case':>9} {'asym max':>10} {'asym gap':>10} {'vs serial':>10} "
      f"{'men low':>8} {'men up':>8} {'men mid':>8} {'wall low':>9} {'wall up':>8} {'max|U|':>7}")
for t in ("5e-05", "0.0001", "0.0005", "0.001", "0.0015", "0.002"):
    if not os.path.isdir(os.path.join(SP, "serial", t)):
        continue
    ref = read("serial", t, "alpha.wetting")
    for case in CASES:
        if not os.path.isdir(os.path.join(SP, case, t)):
            print(f"{float(t)*1e3:7.3f} {case:>9}  (no data)")
            continue
        a = read(case, t, "alpha.wetting")
        U = read(case, t, "U", vec=True)
        mir = a[::-1]
        asym = np.abs(a - mir).max()
        asym_gap = np.abs(a[8:16] - mir[8:16]).max()
        d = np.abs(a - ref).max()
        # wall front: first x where the wall row next to the gap (k=7 / k=16) drops below 0.1 (porous saturation)
        def wf(k):
            idx = np.where(a[k, :97] < 0.1)[0]
            return idx[0] * 0.02 if len(idx) else np.nan
        print(f"{float(t)*1e3:7.3f} {case:>9} {asym:10.2e} {asym_gap:10.2e} {d:10.2e} "
              f"{meniscus(a, 8):8.4f} {meniscus(a, 15):8.4f} {0.5*(meniscus(a, 11)+meniscus(a, 12)):8.4f} "
              f"{wf(7):9.3f} {wf(16):8.3f} {np.linalg.norm(U, axis=2).max():7.3f}")
