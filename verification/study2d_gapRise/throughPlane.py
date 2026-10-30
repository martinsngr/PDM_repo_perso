#!/usr/bin/env python3
"""throughPlane.py <run>  -  turns a cut-REV run of makeCases.sh into the previous student's direction (README.md, S9): water under the fabric, rising
through the thickness. The 3 padding layers below the fabric full of water, every other free cell air, bath on `bottom` (J), edge y = 0 closed."""
import re
import sys

run = sys.argv[1]


def block(path, patch, body):
    s = open(path).read()
    s, n = re.subn(rf"(\n    {patch}\n    \{{\n).*?(\n    \}}\n)", lambda m: m.group(1) + body + m.group(2), s, count=1, flags=re.S)
    assert n == 1, (path, patch)
    open(path, "w").write(s)


def values(path):
    L = open(path).read().split("\n")
    i = next(k for k, l in enumerate(L) if l.startswith("internalField"))
    n = int(L[i + 1])
    assert L[i + 2] == "("
    return L, i + 3, n


block(f"{run}/0/alpha.wetting", "inlet", "        type            zeroGradient;")
block(f"{run}/0/alpha.wetting", "bottom", "        type            inletOutlet;\n        inletValue      uniform 1;\n        value           uniform 1;")
block(f"{run}/0/p", "inlet", "        type            fixedFluxPressure;\n        gradient        uniform 0;\n        value           uniform 0;")
block(f"{run}/0/U", "inlet", "        type            noSlip;")
tp = f"{run}/constant/transportProperties"
s = open(tp).read()
s, n = re.subn(r"^waterOnlyPatches \(inlet\);", "waterOnlyPatches (bottom);", s, flags=re.M)
assert n == 1
open(tp, "w").write(s)
LC, iC, nC = values(f"{run}/0/C")
La, ia, na = values(f"{run}/0/alpha.wetting")
Le, ie, ne = values(f"{run}/0/eps")
assert nC == na == ne
v = open(f"{run}/system/blockMeshDict").read().split("vertices", 1)[1].split(");", 1)[0]
zv = sorted({float(t.split()[2]) for t in re.findall(r"\(\s*([-\d.e+]+\s+[-\d.e+]+\s+[-\d.e+]+)\s*\)", v)})
nw = 0
for k in range(nC):
    if float(Le[ie + k]) > 0.99:
        z = float(LC[iC + k].strip("()").split()[2])
        La[ia + k] = "1" if z < zv[1] else "0"
        nw += z < zv[1]
open(f"{run}/0/alpha.wetting", "w").write("\n".join(La))
print(f"{run}: bath on bottom, {nw} padding cells full of water, the other free cells air, z of the fabric box {zv[1]*1e3:.3f} to {zv[2]*1e3:.3f} mm")
