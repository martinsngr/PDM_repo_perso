#!/bin/bash
# buildCase.sh  -  mesh and initial fields of a study 2e case (README.md), called by the case's Allpre:
#     [PAD_GRADED="N Q"] ../buildCase.sh <case> <NB> <NA> [box|band]
# NA = fabric rows above the bath plane y0 = 0.333 mm: 58 (y 1.496 mm, R0_inlet and B_layer) or 133 (y 3.0 mm, the full
#   length of job 3068, B_full).
# NB = 0: job 3068 (REV_midbath, Allpre of 2026-11-02) cut at y0 + NA rows: same cells, same patches (inlet = bath
#   plane y0, water only by J; inletPad, outlet closed; top/bottom open; sideA/B cyclic), same initFields.py options.
# NB > 0: the same fabric cells plus NB rows of free cells below y0, full of water (the bath), with the inlet at the
#   bottom of that layer and the z faces of the layer closed (patch bathWall); the fabric fields and its initial alpha
#   are copied from an NB = 0 twin built beside the case (bathLayer.py), so above y0 the case starts as job 3068.
# box (with NB > 0, option 1 of 2026-11-04): the layer cells under the padding are removed at the end (topoSet +
#   subsetMesh, fields mapped), so the bath lies under the fabric box only; the exposed faces (floor of the padding at y0,
#   z sides of the layer) join bathWall. In B_full the bath under the padding touched the open top/bottom faces and leaked.
# band (with NB > 0, 2026-11-05): as box, but the bath lies only under the yarn band of the bath plane: z between the
#   lowest and highest yarn cell of the first fabric row above y0 (layers 6-12 of the box at y0 = 0.333 mm). The open
#   space above and below the yarns (and the padding) gets a closed floor at y0 (bathWall) and starts dry: its initial
#   water column is removed (alpha 0 in the free cells above y0 outside the band). In Bbox_full (box) the outermost box
#   layers held a bath surface beside the fabric, flooded at 5-8 ms and fed the padding, which leaked.
# PAD_GRADED="N Q" (environment, also used by the R0 twin): graded padding of N layers growing by Q (build_mesh.py
#   --pad); unset: 3 layers of the box cell size, as job 3068.
# Overwrites the mesh and 0/ of <case>. Python: $PY, else the repo .venv (numpy, trimesh, rtree, embreex).
set -e
here=$(cd "${0%/*}" && pwd)
case=$(cd "$1" && pwd)
NB=$2
NA=$3
MODE=${4:-}
PY=${PY:-$here/../../.venv/bin/python}
[ -x "$PY" ] || PY=python3
. "$WM_PROJECT_DIR/bin/tools/RunFunctions"

cd "$case"
rm -rf constant/polyMesh 0 system/blockMeshDict system/rev_domain.json system/topoSetDict system/createPatchDict
rm -f log.build_mesh log.blockMesh log.checkMesh log.topoSet log.createPatch log.postProcess.writeCellCentres log.initFields \
      log.bathLayer log.r0twin log.topoSet.box log.subsetMesh log.checkMesh.box system/topoSetDict.box \
      log.writeCellCentres.band log.band
"$PY" "$here/build_mesh.py" . --below "$NB" --above "$NA" ${PAD_GRADED:+--pad $PAD_GRADED} > log.build_mesh 2>&1 \
    || { cat log.build_mesh; exit 1; }
runApplication blockMesh

if [ "$NB" -gt 0 ]; then
    # z faces of the bath layer (top/bottom faces below y0) -> closed patch bathWall; no 0/ yet, so no field is remapped
    y0=$("$PY" -c "import json; print(json.load(open('$here/../../meshing_strat_trial/REV_midbath/rev_domain.json'))['min_m'][1])")
    mv 0 0.build
    cat > system/topoSetDict <<EOT
FoamFile { version 2.0; format ascii; class dictionary; object topoSetDict; }
actions
(
    { name bathWallFaces; type faceSet; action new;    source patchToFace; sourceInfo { name "(top|bottom)"; } }
    { name bathWallFaces; type faceSet; action subset; source boxToFace;   sourceInfo { box (-1 -1 -1) (1 $y0 1); } }
);
EOT
    cat > system/createPatchDict <<EOT
FoamFile { version 2.0; format ascii; class dictionary; object createPatchDict; }
pointSync false;
patches
(
    { name bathWall; patchInfo { type patch; } constructFrom set; set bathWallFaces; }
);
EOT
    runApplication topoSet
    runApplication createPatch -overwrite
    rm -rf constant/polyMesh/sets
    mv 0.build 0
fi

runApplication checkMesh
cp 0.orig/* 0/
runApplication -s writeCellCentres postProcess -func writeCellCentres -time 0
closed="--closed-patch outlet --closed-patch inletPad"
[ "$NB" -gt 0 ] && closed="$closed --closed-patch bathWall"
"$PY" "$here/../../meshing_strat_trial/tools/initFields.py" $closed --free-fill 1e-4 --sat-height 1e-4 --porous-in 1 \
    > log.initFields 2>&1 || { cat log.initFields; exit 1; }
cat log.initFields
rm -f 0/C 0/Cx 0/Cy 0/Cz

if [ "$NB" -gt 0 ]; then
    # R0 twin for the fabric fields and the initial alpha above y0, beside the case (its controlDict includes ../../tools)
    twin="$here/_r0_$(basename "$case")"
    rm -rf "$twin"
    mkdir "$twin"
    cp -r 0.orig constant system "$twin/"
    rm -rf "$twin/constant/polyMesh" "$twin/system/topoSetDict" "$twin/system/createPatchDict"
    "$here/buildCase.sh" "$twin" 0 "$NA" > log.r0twin 2>&1 || { cat log.r0twin; exit 1; }
    "$PY" "$here/bathLayer.py" . "$twin" > log.bathLayer 2>&1 || { cat log.bathLayer; exit 1; }
    cat log.bathLayer
    rm -rf "$twin" log.r0twin
fi

if { [ "$MODE" = box ] || [ "$MODE" = band ]; } && [ "$NB" -gt 0 ]; then
    # box (option 1): keep the bath under the fabric box only (z between the padding blocks, from blockMeshDict);
    # band: only under the yarn band of the first fabric row above y0. Last step, so that the fields written on the full
    # grid above are mapped by subsetMesh
    if [ "$MODE" = box ]; then
    read -r zlo zhi <<< "$("$PY" -c "
import re
v = open('system/blockMeshDict').read().split('vertices', 1)[1].split(');', 1)[0]
z = sorted({float(t.split()[2]) for t in re.findall(r'\(\s*([-\d.e+]+\s+[-\d.e+]+\s+[-\d.e+]+)\s*\)', v)})
print(z[1], z[2])")"
    else
    runApplication -s band postProcess -func writeCellCentres -time 0
    read -r zlo zhi <<< "$("$PY" - "$y0" <<'PYEOF'
import re, sys
import numpy as np
y0 = float(sys.argv[1])
def internal(path, vec=False):
    body = open(path).read().split("internalField", 1)[1]
    n = int(re.search(r">\s*(\d+)\s*\(", body).group(1))
    data = body.split("(", 1)[1]
    if vec:
        return np.array([t.split() for t in re.findall(r"\(([^()]+)\)", data)[:n]], float)
    return np.array(data.split(")", 1)[0].split()[:n], float)
C = internal("0/C", vec=True)
P = internal("0/eps") <= 0.99
dy = 2.667e-3 / 133
row1 = P & (C[:, 1] > y0) & (C[:, 1] < y0 + 0.75 * dy)
v = open("system/blockMeshDict").read()
nbox = int(re.findall(r"hex \(4 5 6 7 8 9 10 11\) \(\d+ \d+ (\d+)\)", v)[0])
z = sorted({float(t.split()[2]) for t in re.findall(r"\(\s*([-\d.e+]+\s+[-\d.e+]+\s+[-\d.e+]+)\s*\)",
                                                  v.split("vertices", 1)[1].split(");", 1)[0])})
dz = (z[2] - z[1]) / nbox
print(C[row1, 2].min() - dz / 2, C[row1, 2].max() + dz / 2)
PYEOF
)"
    rm -f 0/C 0/Cx 0/Cy 0/Cz
    echo "band: bath under z $zlo to $zhi m (yarn cells of the first fabric row above y0)"
    fi
    cat > system/topoSetDict.box <<EOT
FoamFile { version 2.0; format ascii; class dictionary; object topoSetDict; }
actions
(
    { name keep; type cellSet; action new;      source boxToCell; sourceInfo { box (-1 -1 -1) (1 1 1); } }
    { name keep; type cellSet; action delete;   source boxToCell; sourceInfo { box (-1 -1 -1) (1 $y0 $zlo); } }
    { name keep; type cellSet; action delete;   source boxToCell; sourceInfo { box (-1 -1 $zhi) (1 $y0 1); } }
);
EOT
    runApplication -s box topoSet -dict system/topoSetDict.box
    runApplication subsetMesh keep -overwrite -patch bathWall
    rm -rf constant/polyMesh/sets
    # U, p and the phase velocities from 0.orig again (their patch entries are regular expressions, subsetMesh writes
    # them out per patch)
    cp 0.orig/* 0/
    if [ "$MODE" = band ]; then
        # the open space above and below the yarns starts dry: no bath under it (alpha 0 in the free cells above y0
        # outside the band; padding cells are already 0)
        runApplication -s band2 postProcess -func writeCellCentres -time 0
        "$PY" - "$y0" "$zlo" "$zhi" > log.band <<'PYEOF'
import re, sys
import numpy as np
y0, zlo, zhi = map(float, sys.argv[1:4])
def split(path):
    txt = open(path).read()
    head, body = txt.split("internalField", 1)
    n = int(re.search(r">\s*(\d+)\s*\(", body).group(1))
    pre, data = body.split("(", 1)
    vals, post = data.split(")", 1)
    return head, pre, vals, post, n
body = open("0/C").read().split("internalField", 1)[1]
nC = int(re.search(r">\s*(\d+)\s*\(", body).group(1))
C = np.array([t.split() for t in re.findall(r"\(([^()]+)\)", body.split("(", 1)[1])[:nC]], float)
he, pe, ve, poe, ne = split("0/eps")
eps = np.array(ve.split()[:ne], float)
ha, pa, va, poa, na = split("0/alpha.wetting")
a = np.array(va.split()[:na], float)
assert nC == ne == na
free = eps > 0.99
out = free & (C[:, 1] > y0) & ((C[:, 2] < zlo) | (C[:, 2] > zhi))
print(f"band: alpha set to 0 in {int((out & (a > 0)).sum())} free cells above y0 outside z {zlo:.6g}..{zhi:.6g} m "
      f"({a[out].sum():.1f} cell volumes of initial water removed); free cells above y0 in the band with alpha > 0.5: "
      f"{int((free & (C[:, 1] > y0) & ~out & (a > 0.5)).sum())}; bath cells below y0: {int((C[:, 1] < y0).sum())}, "
      f"min alpha {a[C[:, 1] < y0].min():.3g}")
a[out] = 0.0
open("0/alpha.wetting", "w").write(ha + "internalField" + pa + "(\n" + "\n".join(f"{v:.8g}" for v in a) + "\n)" + poa)
PYEOF
        cat log.band
        rm -f 0/C 0/Cx 0/Cy 0/Cz
    fi
    runApplication -s box checkMesh
    "$PY" - <<'PYEOF'
import re
b = open("constant/polyMesh/boundary").read()
n = {m.group(1): int(m.group(2)) for m in re.finditer(r"\n\s*(\w+)\s*\{[^}]*?nFaces\s+(\d+);", b)}
cells = re.search(r"nCells:\s*(\d+)", open("constant/polyMesh/owner").read()).group(1)
print(f"box: {int(cells):,} cells; patch faces: " + ", ".join(f"{k} {v}" for k, v in n.items()))
PYEOF
fi
