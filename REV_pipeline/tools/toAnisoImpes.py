#!/usr/bin/env python3
"""toAnisoImpes.py [case]  -  turns a hybridPorousInterFoam REV case with a tensor K into an anisoImpesFoam case of its
yarns only (REV_pipeline/cases/anisoA), after `topoSet` (cellSet porous) and `subsetMesh porous -overwrite`:
  - constant/polyMesh/boundary: the exposed faces (patch oldInternalFaces) become the patch yarnSurface, type symmetry
    (zero flux for anisoImpesFoam without gravity: zero normal gradient of p and Sb, diagonal K)
  - 0/Sb: internal field = the subset 0/alpha.wetting, boundary conditions of 0.orig/Sb
  - constant/K: internal field = the subset 0/K (volTensorField), boundary values zeroGradient (constraint patches
    by their type)
  - 0/p, 0/Ua, 0/Ub: copied from 0.orig
  - removed from 0/: the hybrid's alpha.wetting, U, Uwetting, UnonWetting, K, p; kept for the analysis scripts: eps,
    yarnID, fYarn (their boundary field rewritten for the new patches)
Needs no OpenFOAM import: plain text on the ascii files of subsetMesh."""
import os
import re
import shutil
import sys

case = sys.argv[1] if len(sys.argv) > 1 else "."
GENERIC_BC = """boundaryField
{
    #includeEtc "caseDicts/setConstraintTypes"
    ".*"
    {
        type            zeroGradient;
    }
}

// ************************************************************************* //
"""


def internal_block(path):
    """the 'internalField ...;' entry of an ascii field file, verbatim"""
    s = open(path).read()
    i = s.index("internalField")
    j = s.index("\nboundaryField", i)
    return s[i:j].rstrip() + "\n"


# 1. the exposed faces: oldInternalFaces -> yarnSurface, type symmetry
bpath = os.path.join(case, "constant/polyMesh/boundary")
b = open(bpath).read()
m = re.search(r"\n(\s*)oldInternalFaces\s*\n\s*\{(.*?)\n\s*\}", b, flags=re.S)
if not m:
    raise SystemExit("no patch oldInternalFaces in constant/polyMesh/boundary: run subsetMesh porous -overwrite first")
ind = m.group(1)
body = [l for l in m.group(2).split("\n") if l.strip() and not re.match(r"\s*(type|inGroups|physicalType)\b", l)]
new = (f"\n{ind}yarnSurface\n{ind}{{\n{ind}    type            symmetry;\n{ind}    inGroups        List<word> 1(symmetry);\n"
       + "\n".join(body) + f"\n{ind}}}")
b = b[:m.start()] + new + b[m.end():]
open(bpath, "w").write(b)
nfaces = re.search(r"nFaces\s+(\d+);", new).group(1)
print(f"patch oldInternalFaces -> yarnSurface (symmetry), {nfaces} faces")

# 2. Sb from the subset alpha.wetting
z = os.path.join(case, "0")
sb = open(os.path.join(case, "0.orig/Sb")).read()
sb, n = re.subn(r"internalField\s+uniform\s+[^;]+;\n", lambda _: internal_block(os.path.join(z, "alpha.wetting")), sb, count=1)
assert n == 1
open(os.path.join(z, "Sb"), "w").write(sb)

# 3. constant/K from the subset 0/K
k = open(os.path.join(z, "K")).read()
if "volTensorField" not in k.split("internalField", 1)[0]:
    raise SystemExit("0/K is not a volTensorField: anisoImpesFoam needs a tensor K (build_fields.py --k-mode tensor)")
head = k[:k.index("dimensions")].replace('location    "0";', 'location    "constant";')
dims = re.search(r"dimensions\s+[^;]+;", k).group(0)
open(os.path.join(case, "constant/K"), "w").write(head + dims + "\n\n" + internal_block(os.path.join(z, "K")) + "\n"
                                                    + GENERIC_BC)

# 4. p, Ua, Ub from 0.orig; the hybrid's fields out; check fields with the new patches
for f in ("p", "Ua", "Ub"):
    shutil.copy(os.path.join(case, "0.orig", f), os.path.join(z, f))
for f in ("alpha.wetting", "U", "Uwetting", "UnonWetting", "K"):
    if os.path.isfile(os.path.join(z, f)):
        os.remove(os.path.join(z, f))
for f in ("eps", "yarnID", "fYarn"):
    p = os.path.join(z, f)
    if os.path.isfile(p):
        s = open(p).read()
        open(p, "w").write(s[:s.index("boundaryField")] + GENERIC_BC)
n_cells = int(re.search(r"(\d+)\s*\(", internal_block(os.path.join(z, "Sb"))).group(1))
print(f"0/Sb, constant/K: {n_cells:,} cells; 0/p, 0/Ua, 0/Ub from 0.orig; 0/: {sorted(os.listdir(z))}")
