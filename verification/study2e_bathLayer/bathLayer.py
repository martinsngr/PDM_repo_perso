#!/usr/bin/env python3
"""bathLayer.py  -  initial fields of B_layer from its R0 twin (study 2e).
    python bathLayer.py <B case> <R0 case>
Both cases are built by buildCase.sh on the same grid (build_mesh.py); B has NB extra rows below the bath plane y0.
  - checks that B's eps, fYarn and yarnID above y0 (from build_fields.py) equal those of R0 cell by cell
  - eps, K, fYarn, yarnID: above y0 from R0; the NB layer rows free (eps 1, K 1 m2 = K_VOID, fYarn 0, yarnID -1);
    written with zeroGradient on every non-cyclic patch (bathWall included)
  - alpha.wetting: the internal field of R0 above y0 (initFields.py: yarns 0.99 over 0.1 mm then the ramp, 0.1 mm water
    column in the free box cells, padding air), the layer rows water (alpha 1); B's boundaryField (initFields.py on B) kept
Cell order x fastest, then y, then z (blockMesh, z-stacked blocks)."""
import os
import re
import sys

import numpy as np

B, R0 = sys.argv[1], sys.argv[2]


def dims(case):
    bm = open(os.path.join(case, "system/blockMeshDict")).read()
    b = re.findall(r"hex\s*\([\d\s]+\)\s*\((\d+)\s+(\d+)\s+(\d+)\)", bm)
    return int(b[0][0]), int(b[0][1]), sum(int(x[2]) for x in b)


def read(case, name):
    txt = open(os.path.join(case, "0", name)).read()
    head, body = txt.split("internalField", 1)
    n = int(re.search(r">\s*(\d+)\s*\(", body).group(1))
    vals = body.split("(", 1)[1].split(")", 1)[0].split()[:n]
    bf = "boundaryField" + body.split("boundaryField", 1)[1]
    return head, np.array(vals, float), bf


def patches(case):
    txt = open(os.path.join(case, "constant/polyMesh/boundary")).read()
    return re.findall(r"\n\s*(\w+)\s*\{\s*type\s+(\w+);", txt.split("(", 1)[1])


def write(case, name, head, vals, bf):
    with open(os.path.join(case, "0", name), "w") as fh:
        fh.write(head + "internalField   nonuniform List<scalar>\n" + f"{len(vals)}\n(\n")
        fh.write("\n".join(f"{v:.8g}" for v in vals) + "\n)\n;\n\n" + bf)


nB, nR = dims(B), dims(R0)
assert nB[0] == nR[0] and nB[2] == nR[2] and nB[1] > nR[1], (nB, nR)
NB = nB[1] - nR[1]


def grid(v, n):
    return v.reshape(n, order="F")


# fabric fields of B above y0 against R0
for name in ("eps", "fYarn", "yarnID"):
    vb = grid(read(B, name)[1], nB)[:, NB:, :]
    vr = grid(read(R0, name)[1], nR)
    d = np.abs(vb - vr).max()
    print(f"{name}: B above y0 vs R0, max |difference| {d:.3g}")
    assert d < 1e-6, f"{name} differs: B and R0 are not on the same grid"

bf_plain = "boundaryField\n{\n" + "".join(
    f"    {p}\n    {{\n        type {'cyclic' if t == 'cyclic' else 'zeroGradient'};\n    }}\n"
    for p, t in patches(B)) + "}\n"
layer_value = {"eps": 1.0, "K": 1.0, "fYarn": 0.0, "yarnID": -1.0, "alpha.wetting": 1.0}
for name, value in layer_value.items():
    head, vr, bfR = read(R0, name)
    out = np.full(nB, value)
    out[:, NB:, :] = grid(vr, nR)
    if name == "alpha.wetting":
        head, _, bf = read(B, name)          # boundaryField from initFields.py on B (bathWall, inlet of the layer)
    else:
        bf = bf_plain
    write(B, name, head, out.ravel(order="F"), bf)

eps = grid(read(B, "eps")[1], nB)
a = grid(read(B, "alpha.wetting")[1], nB)
P = eps <= 0.99
print(f"B: {np.prod(nB):,} cells, {NB} layer rows ({NB * nB[0] * nB[2]:,} cells, water); porous {P.sum():,}, "
      f"free {(~P).sum():,}; free water cells above y0 {int(((~P) & (a > 0.5))[:, NB:, :].sum()):,}")
