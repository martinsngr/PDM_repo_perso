#!/bin/bash
# Runs the given truncated-REV run folders (makeREVcut.sh) one after the other, N cores each (caseSetup), with the
# installed solver (HPIF, default hybridPorousInterFoam): serial precompile of the coded function objects (inside
# mpirun the compilation aborts), decomposePar, mpirun, reconstructPar. Logs through ../runTools.sh (in /tmp during
# the run).
#     ./runCut.sh T0_cut_lowpc_t60 ...
cd "${0%/*}" || exit 1
. ../runTools.sh
HPIF=${HPIF:-hybridPorousInterFoam}
for r in "$@"; do
    [ -d "$r" ] || { echo "no run folder $r"; continue; }
    (
        cd "$r" || exit 1
        N=$(foamDictionary -entry N -value caseSetup)
        "$HPIF" -postProcess -time 0 > log.precompile 2>&1 || { echo "$r: precompile failed"; exit 1; }
        rm -f liquidBalance.csv waterBudget.csv
        decomposePar -force > log.decomposePar 2>&1 || { echo "$r: decomposePar failed"; exit 1; }
        runTmpLog log.hybridPorousInterFoam mpirun -np "$N" "$HPIF" -parallel
        status=$?
        reconstructPar > log.reconstructPar 2>&1
        echo "$r: solver exit $status"
    )
done
