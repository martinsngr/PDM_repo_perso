#!/usr/bin/env python3
"""
04_check_periodicity.py  -  are the opposite faces of the REV consistent?

Run from the OpenFOAM case directory, after 03_build_fields.py:
    python3 04_check_periodicity.py            # checks field fYarn
    python3 04_check_periodicity.py eps

Across a cyclic pair, the first cell layer (j = 0) touches the last one (j = ny-1).
For the plain-weave REV cut through yarn centrelines, the two layers are mirror
images about the cut plane, so their fields should be (almost) equal.
A large difference means the geometry is not periodic -> cyclic BCs would be wrong.
"""
import re
import sys

import numpy as np

field = sys.argv[1] if len(sys.argv) > 1 else "fYarn"

bm = open("system/blockMeshDict").read()
n = tuple(int(v) for v in re.search(r"hex\s*\([\d\s]+\)\s*\((\d+)\s+(\d+)\s+(\d+)\)", bm).groups())

txt = open(f"0/{field}").read()
body = txt.split("internalField", 1)[1]
count = int(re.search(r">\s*(\d+)\s*\(", body).group(1))
values = body.split("(", 1)[1].split(")", 1)[0].split()
f = np.array(values[:count], dtype=float)
assert f.size == np.prod(n), f"{f.size} values but mesh is {n}"
f = f.reshape(n, order="F")                      # OpenFOAM order: x fastest, then y, then z

print(f"Field {field}, mesh {n[0]} x {n[1]} x {n[2]}")
for axis, name in enumerate("xyz"[:2]):
    first = np.take(f, 0, axis=axis)
    last = np.take(f, -1, axis=axis)
    d = np.abs(first - last)
    print(f"  {name}-faces: max |diff| = {d.max():.3f}   mean |diff| = {d.mean():.4f}   "
          f"cells with |diff| > 0.1: {np.sum(d > 0.1)} of {d.size}")
print("\nExpect small mean differences; a few isolated cells near crossovers are normal.")
print("Whole rows/regions differing means the REV is not periodic.")