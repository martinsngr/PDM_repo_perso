#!/bin/bash
# buildCase.sh  -  mesh and initial fields of a study 2e case (README.md), called by the case's Allpre:
#     ../buildCase.sh <case> <NB> <NA>
# NA = fabric rows above the bath plane y0 = 0.333 mm: 58 (y 1.496 mm, R0_inlet and B_layer) or 133 (y 3.0 mm, the full
#   length of job 3068, B_full).
# NB = 0: job 3068 (REV_midbath, Allpre of 2026-11-02) cut at y0 + NA rows: same cells, same patches (inlet = bath
#   plane y0, water only by J; inletPad, outlet closed; top/bottom open; sideA/B cyclic), same initFields.py options.
# NB > 0: the same fabric cells plus NB rows of free cells below y0, full of water (the bath), with the inlet at the
#   bottom of that layer and the z faces of the layer closed (patch bathWall); the fabric fields and its initial alpha
#   are copied from an NB = 0 twin built beside the case (bathLayer.py), so above y0 the case starts as job 3068.
# Overwrites the mesh and 0/ of <case>. Python: $PY, else the repo .venv (numpy, trimesh, rtree, embreex).
set -e
here=$(cd "${0%/*}" && pwd)
case=$(cd "$1" && pwd)
NB=$2
NA=$3
PY=${PY:-$here/../../.venv/bin/python}
[ -x "$PY" ] || PY=python3
. "$WM_PROJECT_DIR/bin/tools/RunFunctions"

cd "$case"
rm -rf constant/polyMesh 0 system/blockMeshDict system/rev_domain.json system/topoSetDict system/createPatchDict
rm -f log.build_mesh log.blockMesh log.checkMesh log.topoSet log.createPatch log.postProcess.writeCellCentres log.initFields \
      log.bathLayer log.r0twin
"$PY" "$here/build_mesh.py" . --below "$NB" --above "$NA" > log.build_mesh 2>&1 || { cat log.build_mesh; exit 1; }
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
