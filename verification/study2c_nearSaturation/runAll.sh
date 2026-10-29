#!/bin/bash
# Runs the given run folders of this study in parallel, one serial solver each, with the installed solver
# (HPIF, default hybridPorousInterFoam). Logs through ../runTools.sh (in /tmp during the run).
#     ./runAll.sh N0_lowpc_S091 N1_lowpc_S097 ...
cd "${0%/*}" || exit 1
export HPIF=${HPIF:-hybridPorousInterFoam}
for r in "$@"; do
    [ -d "$r" ] || { echo "no run folder $r"; continue; }
    ( cd "$r" && ./run > run.out 2>&1; echo "$r exit $?" ) &
done
wait
