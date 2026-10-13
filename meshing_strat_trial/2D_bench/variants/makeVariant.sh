#!/bin/bash
# makeVariant.sh <variant> <mode> [value]
#
# Bench variant = copy of ../ (2D_bench, after ../Allpre) with ONE change,
# run serially in variants/<variant>_<mode>/ (open <variant>_<mode>.foam in ParaView).
#   mode steps [N]  : N time steps (default 10), fields written at every step
#   mode run   [T]  : up to T s (default 2e-4), fields written every T/10 (or every $WRITE s)
# Both modes stop early if dt collapses (minDeltaTStop, ../../tools/stopGuard).
# Variants (see ../../NOTES.md, bench debugging):
#   base      bench as is (contact angle off, sigma 0.072, VG pc0 5000 m 0.5, ramp)
#   ca90      activatePorousContactAngle 1 (theta0 90), as Boubaker et al. 2026
#   sigma0    sigma 0: no free-interface surface tension
#   pcMild    VG pc0 1000 Pa, m 0.8 (Boubaker et al. 2026)
#   noRamp    no inlet ramp: dry everywhere, wet inlet face only
#   airZero0  openPorousAirZero 0 (p = 0 on porous faces of open patches)
#   fullSlab  porous everywhere (no free cells): must behave as the 1D case
#   paperLike ca90 + pcMild + no ramp + dry value 0 (Boubaker et al. initial state)
#   closedTB  top/bottom closed walls (U, Uwetting, UnonWetting 0, p fixedFluxPressure, alpha zeroGradient)
#   fullSlabClosed  fullSlab + closedTB: must reproduce the 1D case (control of the bench itself)
#   gapInletAir     free (gap) faces of the inlet supply air (alpha_b 0) instead of reservoir water
#   yarnInletFixed  yarn part of the inlet as its own patch inletYarn, alpha fixedValue 0.99 (reservoir state
#                   kept on outflow too; p from pOpenAir with that alpha)
#   plic            div(phi,alpha) Gauss PLIC interfaceCompression vanLeer 1 (geometric VoF on free faces)
# Referee tests of the yarn/gap interface (all four patches closed walls, no reservoir):
#   R1staticWet       yarn uniform alpha 0.5, air gaps: nothing should move
#   R2waterGap        dry yarn, top gap (z >= 0.22 mm) full of water: the yarn should imbibe from the gap
#   R3closedRamp      bench ramp, inlet closed: water redistributes inside the yarn only
#   R3closedRampSlab  same without gaps (all porous): reference for R3closedRamp
# #2 cyclic test (top/bottom cyclic pair, inlet/outlet closed, bench ramp):
#   cycA  slab z 0.06-0.22 mm (all porous/free faces internal; the gap wraps through the cyclic patch)
#   cycB  slab z 0-0.16 mm (porous/free faces on the cyclic patch); = cycA shifted by 3 cells
# SOLVER=<binary> TAG=<tag> ./makeVariant.sh ...: run another solver build into <variant>_<mode>_<tag>/.
# ADD="KEY VALUE;...": append transportProperties keywords.
# PFDF=1: add 'porousFreeDarcyFaces on;' (change G) if missing (on by default in the bench since 2026-10-12).
# Solver log in /tmp during the run (../../tools/runTools.sh), then in the variant folder.
cd "${0%/*}" || exit 1
. "$WM_PROJECT_DIR/bin/tools/RunFunctions"
. ../../tools/runTools.sh
PY=${PY:-$(cd ../../.. && pwd)/.venv/bin/python}
[ -x "$PY" ] || PY=python3

v=$1; mode=${2:-steps}; val=$3
d=${v}_${mode}${TAG:+_$TAG}
[ -f ../0/alpha.wetting ] || { echo "run ../Allpre first"; exit 1; }
rm -rf "$d"; mkdir -p "$d"
cp -r ../0 ../constant ../system "$d"/
touch "$d/$d.foam"
cd "$d" || exit 1
tp=constant/transportProperties
cd_=system/controlDict

reinit() { # reinit <initFields options>: new alpha.wetting from eps
    runApplication -s writeCellCentres postProcess -func writeCellCentres -time 0 > /dev/null
    "$PY" ../../../tools/initFields.py "$@" > log.initFields 2>&1 || { cat log.initFields; exit 1; }
    rm -f 0/C 0/Cx 0/Cy 0/Cz
}

closePatches() { # closePatches "top bottom" -> those patches become closed walls in every 0/ field
    CLOSE="$1" "$PY" - <<'PYEOF'
import os, re
close = os.environ["CLOSE"].split()
openp = [p for p in ("inlet", "outlet", "top", "bottom") if p not in close]
wall = {"p": "type fixedFluxPressure; value uniform 0;", "U": "type noSlip;",
        "Uwetting": "type fixedValue; value uniform (0 0 0);", "UnonWetting": "type fixedValue; value uniform (0 0 0);",
        "eps": "type zeroGradient;", "K": "type zeroGradient;", "alpha.wetting": "type zeroGradient;"}
grp = "(" + "|".join(close) + ")"
for f, bc in wall.items():
    s = open("0/" + f).read()
    if openp:
        s = s.replace('"(inlet|outlet|top|bottom)"', '"(' + "|".join(openp) + ')"')
    else:   # no open patch left: drop the regex entry (and its #include block) entirely
        s = re.sub(r'\n    "\(inlet\|outlet\|top\|bottom\)"\n    \{.*?\n    \}', "", s, flags=re.S)
    s = re.sub(r"\n    " + grp + r"\n    \{[^}]*\}", "", s)      # explicit entries (alpha.wetting, eps, K)
    i = s.rindex("}")                                                   # end of boundaryField
    s = s[:i] + '    "' + grp + '"\n    {\n        ' + bc + "\n    }\n" + s[i:]
    open("0/" + f, "w").write(s)
PYEOF
}
closeTB() { closePatches "top bottom"; }
cyclicTB() { # top/bottom -> cyclic pair (new mesh), inlet/outlet -> closed walls (for the #2 cyclic test)
    "$PY" - <<'PYEOF'
import re
s = open("system/blockMeshDict").read()
s = s.replace("    bottom\n    {\n        type patch;", "    bottom\n    {\n        type cyclic;\n        neighbourPatch top;")
s = s.replace("    top\n    {\n        type patch;", "    top\n    {\n        type cyclic;\n        neighbourPatch bottom;")
open("system/blockMeshDict", "w").write(s)
PYEOF
    grep -q "neighbourPatch top" system/blockMeshDict || { echo "cyclicTB: blockMeshDict not changed"; exit 1; }
    rm -rf constant/polyMesh; runApplication blockMesh > /dev/null
    "$PY" - <<'PYEOF'
import re
wall = {"p": "type fixedFluxPressure; value uniform 0;", "U": "type noSlip;",
        "Uwetting": "type fixedValue; value uniform (0 0 0);", "UnonWetting": "type fixedValue; value uniform (0 0 0);",
        "eps": "type zeroGradient;", "K": "type zeroGradient;"}
for f, bc in wall.items():
    s = open("0/" + f).read()
    s = re.sub(r'\n    "\(inlet\|outlet\|top\|bottom\)"\n    \{.*?\n    \}', "", s, flags=re.S)
    s = re.sub(r"\n    (inlet|outlet|top|bottom)\n    \{[^}]*\}", "", s)
    i = s.rindex("}")
    s = s[:i] + '    "(inlet|outlet)"\n    {\n        ' + bc + "\n    }\n" + '    "(top|bottom)"\n    {\n        type cyclic;\n    }\n' + s[i:]
    open("0/" + f, "w").write(s)
PYEOF
}
closeAll() { closePatches "inlet outlet top bottom"; }

splitYarnInlet() { # yarn faces of the inlet (z 0.06-0.22 mm) -> patch inletYarn; 0/ patterns extended
    cat > system/topoSetDict <<'TSEOF'
FoamFile { format ascii; class dictionary; object topoSetDict; }
actions
(
    { name yarnInletFaces; type faceSet; action new; source patchToFace; sourceInfo { name inlet; } }
    { name yarnInletFaces; type faceSet; action subset; source boxToFace; sourceInfo { box (-1e-6 -1 0.00006) (1e-6 1 0.00022); } }
);
TSEOF
    cat > system/createPatchDict <<'CPEOF'
FoamFile { format ascii; class dictionary; object createPatchDict; }
pointSync false;
patches
(
    { name inletYarn; patchInfo { type patch; } constructFrom set; set yarnInletFaces; }
);
CPEOF
    mv 0 0.keep   # createPatch would rewrite the fields (and expand the #include of pOpenAir)
    runApplication topoSet > /dev/null && runApplication createPatch -overwrite > /dev/null || { cat log.topoSet log.createPatch; exit 1; }
    mv 0.keep 0
    sed -i 's/"(inlet|outlet|top|bottom)"/"(inlet|inletYarn|outlet|top|bottom)"/' 0/p 0/U 0/Uwetting 0/UnonWetting 0/eps 0/K
    for f in eps K; do   # written by setFields with explicit patch names: add the new patch
        grep -q inletYarn 0/$f || "$PY" -c "import sys; f=sys.argv[1]; s=open(f).read(); i=s.rindex('}'); open(f,'w').write(s[:i]+'    inletYarn\n    {\n        type            zeroGradient;\n    }\n'+s[i:])" 0/$f
    done
    grep -A3 inletYarn constant/polyMesh/boundary | grep nFaces >> variant.diff
}

case $v in
    base) ;;
    ca90)     sed -i 's/^activatePorousContactAngle 0;/activatePorousContactAngle 1;/' $tp ;;
    sigma0)   sed -i 's/^\(sigma .*\]\) *0.072;/\1  0;/' $tp ;;
    pcMild)   sed -i 's/^\(    pc0 pc0 \[.*\]\) 5000;/\1 1000;/; s/^    m 0.5;/    m 0.8;/' $tp ;;
    noRamp)   reinit --ramp 0 ;;
    airZero0) sed -i 's/^openPorousAirZero 1;/openPorousAirZero 0;/' $tp ;;
    fullSlab) sed -i 's/box (-1 -1 0.00006) (1 1 0.00022);/box (-1 -1 -1) (1 1 1);/' system/setFieldsDict
              runApplication setFields > /dev/null; reinit ;;
    paperLike) sed -i 's/^activatePorousContactAngle 0;/activatePorousContactAngle 1;/; s/^\(    pc0 pc0 \[.*\]\) 5000;/\1 1000;/; s/^    m 0.5;/    m 0.8;/' $tp
              reinit --ramp 0 --s-dry 0 ;;
    closedTB) closeTB ;;
    gapInletAir) reinit --free-in 0 ;;
    R1staticWet) reinit --porous-value 0.5; closeAll ;;
    R2waterGap) reinit --ramp 0 --free-water-above 0.00022; closeAll ;;
    R3closedRamp) closeAll ;;
    R3closedRampSlab) sed -i 's/box (-1 -1 0.00006) (1 1 0.00022);/box (-1 -1 -1) (1 1 1);/' system/setFieldsDict
              runApplication setFields > /dev/null; reinit; closeAll ;;
    yarnInletFixed) splitYarnInlet; reinit --fixed-patch inletYarn ;;
    cycA)     cyclicTB; runApplication setFields > /dev/null; reinit; sed -i 's/type inletOutlet;/type zeroGradient;/' 0/alpha.wetting ;;
    cycB)     cyclicTB; sed -i 's/box (-1 -1 0.00006) (1 1 0.00022);/box (-1 -1 -1) (1 1 0.00016);/' system/setFieldsDict
              runApplication setFields > /dev/null; reinit; sed -i 's/type inletOutlet;/type zeroGradient;/' 0/alpha.wetting ;;
    cycC)     cyclicTB; sed -i 's/box (-1 -1 0.00006) (1 1 0.00022);/box (-1 -1 0.00008) (1 1 0.00024);/' system/setFieldsDict
              runApplication setFields > /dev/null; reinit; sed -i 's/type inletOutlet;/type zeroGradient;/' 0/alpha.wetting ;;   # cycA shifted by 1 cell (control)
    lowDa)    sed -i 's/^darcyFaceMaxDa  0.1;/darcyFaceMaxDa  0.04;/' $tp ;;   # #7 test: porous/free faces (Da 0.05) not Darcy
    plic)     sed -i 's/^\(    div(phi,alpha) *\)Gauss upwind;/\1Gauss PLIC interfaceCompression vanLeer 1;/' system/fvSchemes ;;
    fullSlabClosed) sed -i 's/box (-1 -1 0.00006) (1 1 0.00022);/box (-1 -1 -1) (1 1 1);/' system/setFieldsDict
              runApplication setFields > /dev/null; reinit; closeTB ;;
    *) echo "unknown variant $v"; exit 1 ;;
esac

# PFDF=1: switch on change G (porous/free faces as two-phase Darcy faces) in this variant
if [ "${PFDF:-0}" = 1 ] && ! grep -q "^porousFreeDarcyFaces on;" $tp; then
    sed -i 's/^\(darcyFaceMaxDa .*\)$/\1\nporousFreeDarcyFaces on;/' $tp
    grep -q "^porousFreeDarcyFaces on;" $tp || { echo "PFDF: keyword not added"; exit 1; }
fi

# ADD="KEY VALUE;KEY VALUE;...": extra transportProperties keywords (e.g. the scratch changes H/F'/I of 2026-10-13)
if [ -n "${ADD:-}" ]; then
    printf '\n// added by makeVariant.sh ADD\n%s\n' "$(echo "$ADD" | tr ';' '\n' | sed '/^ *$/d; s/$/;/')" >> $tp
fi

if [ "$mode" = steps ]; then
    sed -i "s/^writeControl .*/writeControl    timeStep;/; s/^writeInterval .*/writeInterval   1;/; s/^endTime .*/endTime         1;/; s/^timePrecision .*/timePrecision   12;/; s/^maxSteps .*/maxSteps        ${val:-10};/" $cd_
else
    T=${val:-2e-4}
    W=${WRITE:-$(python3 -c "print($T/10)")}   # WRITE=<interval>: finer writes (default T/10)
    sed -i "s/^endTime .*/endTime         $T;/; s/^writeInterval .*/writeInterval   $W;/; s/^timePrecision .*/timePrecision   12;/" $cd_
fi
# check that the edit applied: diff against the bench
diff ../../constant/transportProperties $tp > variant.diff; diff ../../system/setFieldsDict system/setFieldsDict >> variant.diff
for f in p U Uwetting UnonWetting; do diff ../../0/$f 0/$f >> variant.diff; done
diff ../../system/fvSchemes system/fvSchemes >> variant.diff; grep -h "generated by" 0/alpha.wetting >> variant.diff
start=$(date +%s)
runTmpLog log.hybridPorousInterFoam ${SOLVER:-hybridPorousInterFoam}
echo "solver: ${SOLVER:-hybridPorousInterFoam}" >> variant.diff
status=$?
echo "$d: exit $status, $(grep -c '^Time =' log.hybridPorousInterFoam) steps, t = $(grep '^Time =' log.hybridPorousInterFoam | tail -1 | cut -d' ' -f3), $(( $(date +%s) - start )) s, $(grep -h 'stopGuard:' log.hybridPorousInterFoam | tail -1)"
# keep the folder small: compiled coded libraries are rebuilt at every run; compress big logs
rm -rf dynamicCode
[ "$(stat -c %s log.hybridPorousInterFoam)" -gt 2000000 ] && gzip -f log.hybridPorousInterFoam
exit 0
