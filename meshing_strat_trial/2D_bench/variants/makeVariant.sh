#!/bin/bash
# makeVariant.sh <variant> <mode> [value]
#
# Bench variant = copy of ../ (2D_bench, after ../Allpre) with ONE change,
# run serially in variants/<variant>_<mode>/ (open <variant>_<mode>.foam in ParaView).
#   mode steps [N]  : N time steps (default 10), fields written at every step
#   mode run   [T]  : up to T s (default 2e-4), fields written every T/10
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
# SOLVER=<binary> TAG=<tag> ./makeVariant.sh ...: run another solver build into <variant>_<mode>_<tag>/.
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

closeTB() { # top/bottom -> closed walls in every 0/ field
    "$PY" - <<'PYEOF'
import re
wall = {"p": "type fixedFluxPressure; value uniform 0;", "U": "type noSlip;",
        "Uwetting": "type fixedValue; value uniform (0 0 0);", "UnonWetting": "type fixedValue; value uniform (0 0 0);",
        "eps": "type zeroGradient;", "K": "type zeroGradient;", "alpha.wetting": "type zeroGradient;"}
for f, bc in wall.items():
    s = open("0/" + f).read()
    s = s.replace('"(inlet|outlet|top|bottom)"', '"(inlet|outlet)"')
    s = re.sub(r"\n    (top|bottom)\n    \{[^}]*\}", "", s)          # alpha.wetting from initFields
    i = s.rindex("}")                                                   # end of boundaryField
    s = s[:i] + "    \"(top|bottom)\"\n    {\n        " + bc + "\n    }\n" + s[i:]
    open("0/" + f, "w").write(s)
PYEOF
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
    fullSlabClosed) sed -i 's/box (-1 -1 0.00006) (1 1 0.00022);/box (-1 -1 -1) (1 1 1);/' system/setFieldsDict
              runApplication setFields > /dev/null; reinit; closeTB ;;
    *) echo "unknown variant $v"; exit 1 ;;
esac

if [ "$mode" = steps ]; then
    sed -i "s/^writeControl .*/writeControl    timeStep;/; s/^writeInterval .*/writeInterval   1;/; s/^endTime .*/endTime         1;/; s/^timePrecision .*/timePrecision   12;/; s/^maxSteps .*/maxSteps        ${val:-10};/" $cd_
else
    T=${val:-2e-4}
    sed -i "s/^endTime .*/endTime         $T;/; s/^writeInterval .*/writeInterval   $(python3 -c "print($T/10)");/; s/^timePrecision .*/timePrecision   12;/" $cd_
fi
# check that the edit applied: diff against the bench
diff ../../constant/transportProperties $tp > variant.diff; diff ../../system/setFieldsDict system/setFieldsDict >> variant.diff
for f in p U Uwetting UnonWetting; do diff ../../0/$f 0/$f >> variant.diff; done
start=$(date +%s)
runTmpLog log.hybridPorousInterFoam ${SOLVER:-hybridPorousInterFoam}
echo "solver: ${SOLVER:-hybridPorousInterFoam}" >> variant.diff
status=$?
echo "$d: exit $status, $(grep -c '^Time =' log.hybridPorousInterFoam) steps, t = $(grep '^Time =' log.hybridPorousInterFoam | tail -1 | cut -d' ' -f3), $(( $(date +%s) - start )) s, $(grep -h 'stopGuard:' log.hybridPorousInterFoam | tail -1)"
# keep the folder small: compiled coded libraries are rebuilt at every run; compress big logs
rm -rf dynamicCode
[ "$(stat -c %s log.hybridPorousInterFoam)" -gt 2000000 ] && gzip -f log.hybridPorousInterFoam
exit 0
