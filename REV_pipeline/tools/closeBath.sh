#!/bin/bash
# closeBath.sh [--layers N] [--axis y|x]  -  the N2c bath of study 2g for a vertical REV case (../README.md, Cases: bath of the
# vertical runs, decided with the user 2026-11-13; ../../verification/study2g_noJ/README.md, N2c_full).
# Moves the bath faces (patch inlet) under the N outermost fabric-box z layers on each side (default 1: the box layers next
# to the padding, whose bath-surface cells carried the parasitic circulation of N2_noJfix / N2_full) to a closed patch
# bathWall, then gives every field of 0/ that lists its patches one by one a bathWall entry (zeroGradient). Generalises
# study 2g's makeCases.sh, where the layers were given by number (z layers 3 and 16 of the plain weave).
#
# Run it from the case folder in Allpre, after build_fields.py and blockMesh, before writeCellCentres and initFields.py:
#     ../../tools/closeBath.sh
#     ... initFields.py ... --closed-patch bathWall ...   (the initial water column is then set only across the narrowed
#                                                          inlet: no bath under the closed layers, as in N2c_full)
# Needs: system/blockMeshDict of build_fields.py with --zpad (three blocks stacked in z: padding, box, padding); the bath
# plane = the min plane of the wicking axis (--axis, default y); 0.orig/U and 0.orig/p closing bathWall themselves (their
# closed-wall entry "(outlet|inletPad|bathWall)": noSlip, fixedFluxPressure). Stops if a closed face lies under a yarn cell,
# if the face count is not N layers x the cells along the bath plane on each side, or if 0/alpha.wetting already exists.
set -e
N=1
AXIS=y
while [ $# -gt 0 ]; do
    case "$1" in
        --layers) N=$2; shift 2 ;;
        --axis) AXIS=$2; shift 2 ;;
        *) echo "closeBath.sh: unknown option $1"; exit 1 ;;
    esac
done
. "$WM_PROJECT_DIR/bin/tools/RunFunctions"
PY=${PY:-$(dirname "$0")/../../.venv/bin/python}
[ -x "$PY" ] || PY=python3
if [ ! -f constant/polyMesh/owner ] || [ ! -f system/blockMeshDict ] || [ ! -f 0/eps ]; then
    echo "closeBath.sh: no mesh or no 0/eps: run build_fields.py and blockMesh first."
    exit 1
fi
if [ -f 0/alpha.wetting ]; then
    echo "closeBath.sh: 0/alpha.wetting exists: run closeBath.sh before initFields.py (with --closed-patch bathWall)."
    exit 1
fi
rm -f log.topoSet.closeBath log.createPatch.closeBath log.checkMesh.closeBath

# 1. the closed faces: on the bath plane, in the N outermost box layers on each side
"$PY" - "$N" "$AXIS" <<'PYEOF'
import re, sys
n, axis = int(sys.argv[1]), sys.argv[2]
ia = {"x": 0, "y": 1}[axis]
v = open("system/blockMeshDict").read()
pts = [tuple(map(float, t.split())) for t in re.findall(r"\(\s*([-\d.e+]+\s+[-\d.e+]+\s+[-\d.e+]+)\s*\)",
                                                         v.split("vertices", 1)[1].split(");", 1)[0])]
blocks = [tuple(map(int, b)) for b in re.findall(r"hex\s*\([^)]*\)\s*\((\d+)\s+(\d+)\s+(\d+)\)", v)]
assert len(blocks) == 3 and blocks[0][2] == blocks[2][2], \
    f"expected 3 blocks stacked in z (padding, box, padding: build_fields.py --zpad), got {blocks}"
npad, nbox = blocks[0][2], blocks[1][2]
z = sorted({p[2] for p in pts})                               # padding | box | padding
assert len(z) == 4, f"expected 4 z levels in the vertices, got {z}"
assert 1 <= n and 2 * n < nbox, f"--layers {n}: the box has {nbox} layers"
a0 = min(p[ia] for p in pts)                                  # the bath plane
dz = (z[2] - z[1]) / nbox
boxes = []
for b in list(range(n)) + list(range(nbox - n, nbox)):
    lo = [-1.0, -1.0, z[1] + (b + 0.25) * dz]                # face centres at z[1] + (b + 0.5) dz; in-plane: the whole
    hi = [1.0, 1.0, z[1] + (b + 0.75) * dz]                  # patch (the domain is mm-sized)
    lo[ia], hi[ia] = a0 - dz / 4, a0 + dz / 4
    boxes.append("({:.9g} {:.9g} {:.9g}) ({:.9g} {:.9g} {:.9g})".format(*lo, *hi))
    print(f"closeBath: box layer {b} (z layer {npad + b} of the padded grid), z {z[1] + b * dz:.6g} to "
          f"{z[1] + (b + 1) * dz:.6g} m, bath plane {axis} = {a0:.6g} m")
open("system/topoSetDict", "w").write(
    "FoamFile { version 2.0; format ascii; class dictionary; object topoSetDict; }\nactions\n(\n"
    f"    {{ name closeBath; type faceSet; action new;    source boxToFace;   sourceInfo {{ boxes ({' '.join(boxes)}); }} }}\n"
    "    { name closeBath; type faceSet; action subset; source patchToFace; sourceInfo { name inlet; } }\n);\n")
open("system/createPatchDict", "w").write(
    "FoamFile { version 2.0; format ascii; class dictionary; object createPatchDict; }\npointSync false;\npatches\n(\n"
    "    { name bathWall; patchInfo { type patch; } constructFrom set; set closeBath; }\n);\n")
PYEOF
runApplication -s closeBath topoSet
runApplication -s closeBath createPatch -overwrite
rm -rf constant/polyMesh/sets
runApplication -s closeBath checkMesh

# 2. checks, and the bathWall entry of the 0/ fields that list their patches one by one (build_fields.py: eps, K, fYarn,
#    yarnID); U and p must close it themselves (0.orig)
"$PY" - "$N" "$AXIS" <<'PYEOF'
import os, re, sys
import numpy as np
n, axis = int(sys.argv[1]), sys.argv[2]
def strip(t):
    return re.sub(r"FoamFile\s*\{.*?\}", "", re.sub(r"/\*.*?\*/", "", t, flags=re.S), count=1, flags=re.S)
b = open("constant/polyMesh/boundary").read()
pat = {m.group(1): (int(m.group(2)), int(m.group(3)))
       for m in re.finditer(r"\n\s*(\w+)\s*\{[^}]*?nFaces\s+(\d+);[^}]*?startFace\s+(\d+);", b)}
blocks = [tuple(map(int, k)) for k in re.findall(r"hex\s*\([^)]*\)\s*\((\d+)\s+(\d+)\s+(\d+)\)",
                                                  open("system/blockMeshDict").read())]
along = blocks[1][0] if axis == "y" else blocks[1][1]         # cells along the bath plane in one z layer
nw, sw = pat["bathWall"]
assert nw == along * 2 * n, f"bathWall has {nw} faces, expected {along} per closed layer x {2 * n} layers"
own = np.array(strip(open("constant/polyMesh/owner").read()).split("(", 1)[1].split(")", 1)[0].split(), int)
eb = open("0/eps").read().split("internalField", 1)[1]
ne = int(re.search(r"(\d+)\s*\(", eb).group(1))
eps = np.array(eb.split("(", 1)[1].split(")", 1)[0].split()[:ne], float)
assert (eps[own[sw:sw + nw]] > 0.99).all(), "a closed bath face lies under a yarn cell: closeBath does not apply as is"
ni, si = pat["inlet"]
ein = eps[own[si:si + ni]]
print(f"closeBath: bathWall {nw} faces (all under free cells); inlet {ni} faces ({(ein <= 0.99).sum()} porous, "
      f"{(ein > 0.99).sum()} free)")
entry = "    bathWall\n    {\n        type zeroGradient;\n    }\n"
for f in sorted(os.listdir("0")):
    path = os.path.join("0", f)
    if not os.path.isfile(path):
        continue
    s = open(path).read()
    if "bathWall" in s or '".*"' in s:
        continue
    assert f not in ("U", "p"), f"0/{f} does not close bathWall: put it in the closed-wall entry of 0.orig/{f}"
    m = re.search(r"\n    inletPad\n    \{\n.*?\n    \}\n", s, re.S)
    assert m, f"0/{f}: no inletPad entry to put bathWall next to"
    open(path, "w").write(s[:m.end()] + entry + s[m.end():])
    print(f"closeBath: 0/{f}: bathWall entry added (zeroGradient)")
PYEOF
