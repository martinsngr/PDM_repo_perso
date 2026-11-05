#!/bin/bash
# Runs the run folders of the tensor K checks side by side (all by default), then the comparisons of README.md.
#   ./runAll.sh                       all (cores: 4 serial runs + 2 x 4 for the cut REV = 12)
#   ./runAll.sh C2_S1_scalar ...      only these runs, then all comparisons whose runs exist
#   ./runAll.sh --compare             comparisons only
cd "${0%/*}" || exit 1
[ -n "$WM_PROJECT_DIR" ] || { echo "OpenFOAM environment not loaded (source /opt/openfoam9/etc/bashrc)"; exit 1; }
PY=../../.venv/bin/python
if [ "$1" != "--compare" ]; then
    runs=("$@")
    [ ${#runs[@]} -eq 0 ] && runs=(C[0-9]*_*/)
    for r in "${runs[@]}"; do
        r=${r%/}
        [ -x "$r/run" ] || { echo "no run script in $r (./makeCases.sh)"; continue; }
        ( "./$r/run" > "$r/run.out" 2>&1; echo "$r: exit $?" ) &
    done
    wait
fi
cmpIf() { [ -d "$1" ] && [ -d "$2" ] && { "$PY" compare.py "$@"; echo; }; }
cmpIf C1_1D_T ../wicking1D/ABC
cmpIf C1_bench_inst C1_bench_T
cmpIf C1_bench_T C2_bench_tensor --expect-differ K Uwetting UnonWetting Ur
cmpIf C2_S1_scalar C2_S1_tensor --expect-differ K Uwetting UnonWetting Ur
cmpIf C3_y_scalar C3_y_tensor --expect-differ K Uwetting UnonWetting Ur
cmpIf C3_y_tensor C3_x_tensor --expect-differ K U Uwetting UnonWetting Ur
cmpIf C3_y_tensor C3_z_tensor --expect-differ K U Uwetting UnonWetting Ur
[ -d C3_y_scalar ] && "$PY" compareScaling.py C3_y_scalar ../wicking1D/ABC 4
[ -d C5_tensor ] && "$PY" compareSeries.py C5_tensor harmonic
[ -d C5_scalar ] && "$PY" compareSeries.py C5_scalar linear
