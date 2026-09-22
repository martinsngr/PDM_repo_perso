#!/bin/bash
# Clean + run every case directory here (CpD*) in series.
# Parameters in each case are assumed to already be set by hand;
# this script just does `./AllClean && ./AllRun.sh` per case.
set -uo pipefail

SUMMARY="summary.log"
: > "$SUMMARY"

shopt -s nullglob
for dest in CpD*level2*/; do
    dest="${dest%/}"
    echo "=== $dest ==="

    (
        cd "$dest" || exit 1
        chmod +x AllClean AllRun.sh decompose makeMesh 2>/dev/null
        ./AllClean
        ./AllRun.sh > AllRun.log 2>&1
    )
    status=$?

    if [ $status -eq 0 ]; then
        echo "$dest: SUCCESS" | tee -a "$SUMMARY"
    else
        echo "$dest: FAILED (exit $status) - see $dest/AllRun.log" | tee -a "$SUMMARY"
    fi
    echo ""
done

echo "=== Mesh convergence run complete. Summary: ==="
cat "$SUMMARY"
