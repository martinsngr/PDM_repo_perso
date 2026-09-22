#!/bin/bash
# Mesh convergence study: clone PW-22-15-0.4-0.5 for each CpD value,
# fix refLe=0 (isolate CpD as the only refinement variable), then run
# the full mesh+solve pipeline (AllRun.sh) for each case in turn.
set -uo pipefail

SOURCE_CASE="PW-22-15-0.4-0.5"
OUTPUT_DIR="mesh_convergence"
CPD_VALUES=(10 12 14 16 18 20)

mkdir -p "$OUTPUT_DIR"

SUMMARY="$OUTPUT_DIR/summary.log"
: > "$SUMMARY"

for cpd in "${CPD_VALUES[@]}"; do
    dest="$OUTPUT_DIR/CpD${cpd}"
    echo "=== Setting up CpD=$cpd in $dest ==="

    if [ -d "$dest" ]; then
        echo "  $dest already exists, skipping copy"
    else
        cp -r "$SOURCE_CASE" "$dest"
    fi

    # Update caseSetup: set this case's CpD, and fix refLe=0 for all cases
    # in the study (so CpD is the only thing varying between them).
    sed -i -E "s/^CpD[[:space:]]+[0-9.]+;/CpD\t${cpd};/" "$dest/caseSetup"
    sed -i -E "s/^refLe[[:space:]]+[0-9.]+;/refLe\t0;/" "$dest/caseSetup"
    echo "  caseSetup updated: CpD=${cpd}, refLe=0"

    echo "=== Running AllRun.sh for CpD=$cpd ==="
    (
        cd "$dest" || exit 1
        chmod +x AllRun.sh AllClean decompose makeMesh
        ./AllRun.sh > AllRun.log 2>&1
    )
    status=$?

    if [ $status -eq 0 ]; then
        echo "CpD=${cpd}: SUCCESS" | tee -a "$SUMMARY"
    else
        echo "CpD=${cpd}: FAILED (exit $status) - see $dest/AllRun.log" | tee -a "$SUMMARY"
    fi
    echo ""
done

echo "=== Mesh convergence study complete. Summary: ==="
cat "$SUMMARY"
