#!/bin/bash
# Runs the given run folders of this study in parallel, N cores each (caseSetup), with the installed solver (HPIF,
# default hybridPorousInterFoam). The logs stay outside the workspace and outside /tmp during the run
# (LOG_DIR, default ~/PDM_results/study2d_logs: a shutdown does not lose them).
#     ./runAll.sh S1_K1e-12_t40 ...
# Rerunning a folder that has processor folders resumes it from its last write (startFrom latestTime); the log of the
# interrupted part stays in LOG_DIR.
cd "${0%/*}" || exit 1
. ../runTools.sh
HPIF=${HPIF:-hybridPorousInterFoam}
export LOG_DIR=${LOG_DIR:-$HOME/PDM_results/study2d_logs}
for r in "$@"; do
    [ -d "$r" ] || { echo "no run folder $r"; continue; }
    (
        cd "$r" || exit 1
        N=$(foamDictionary -entry N -value caseSetup)
        if [ ! -d processor0 ]; then
            "$HPIF" -postProcess -time 0 > log.precompile 2>&1 || { echo "$r: precompile failed"; exit 1; }
            grep -q "^porousFreeAirKrPorous:" log.precompile || { echo "$r: this solver ignores porousFreeAirKrPorous"; exit 1; }
            rm -f liquidBalance.csv waterBudget.csv
            decomposePar -force > log.decomposePar 2>&1 || { echo "$r: decomposePar failed"; exit 1; }
        fi
        runTmpLog log.hybridPorousInterFoam mpirun -np "$N" "$HPIF" -parallel
        status=$?
        reconstructPar -newTimes > log.reconstructPar 2>&1
        echo "$r: solver exit $status"
    ) &
done
wait
