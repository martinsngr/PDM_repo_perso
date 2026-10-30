#!/bin/bash
# Builds the screening runs of this study (README.md) from the truncated REV of study 2c, run T11 (first 0.7 mm of
# the REV_lowpc mesh and initial fields, built there by makeREVcut.sh; K 1e-11, pc0 1000, m 0.4, theta 40, no L).
#     ./makeCases.sh [run ...]       (no argument: all runs of the table below; an existing run folder is replaced)
# Per run: name, yarn K [m2], pc0 [Pa], m, theta0 [deg]. All runs: porousFreeAirKrPorous on, 3 ms, writes every 0.1 ms.
cd "${0%/*}" || exit 1
PY=${PY:-../../.venv/bin/python}
SRC=${SRC:-../study2c_nearSaturation/T11_cut_lowpc_t40}

RUNS="
S1_K1e-12_t40       1e-12 5000 0.5 40
S2_K1e-12_t30       1e-12 5000 0.5 30
S3_K1e-12_lowpc_t40 1e-12 1000 0.4 40
"

[ -f "$SRC/constant/polyMesh/owner" ] && [ -f "$SRC/0/K" ] || { echo "no mesh or 0/K in $SRC"; exit 1; }
want=" $* "
echo "$RUNS" | while read -r name K pc0 m theta; do
    [ -n "$name" ] || continue
    [ $# -eq 0 ] || [[ "$want" == *" $name "* ]] || continue
    case "$name" in S[0-9]*) ;; *) echo "bad run name $name"; exit 1 ;; esac
    rm -rf "./$name"
    mkdir "./$name"
    cp -r "$SRC/0" "$SRC/constant" "$SRC/system" "$SRC/caseSetup" "./$name/"
    "$PY" - "$name" "$K" "$pc0" "$m" "$theta" <<'PYEOF'
import re, sys
name, K, pc0, m, theta = sys.argv[1:6]


def edit(path, pattern, new):
    s = open(path).read()
    s, n = re.subn(pattern, new, s, flags=re.M)
    assert n == 1, f"{path}: {pattern!r} matched {n} times"
    open(path, "w").write(s)


s = open(f"{name}/0/K").read()
s, n = re.subn(r"^1e-11$", K, s, flags=re.M)
assert n > 0
open(f"{name}/0/K", "w").write(s)
tp = f"{name}/constant/transportProperties"
edit(tp, r"^    pc0 pc0 \[1 -1 -2 0 0 0 0\] [^;]+;[^\n]*", f"    pc0 pc0 [1 -1 -2 0 0 0 0] {pc0};")
edit(tp, r"^    m [^;]+;[^\n]*", f"    m {m};")
edit(tp, r"^theta0\s+[^;]+;[^\n]*", f"theta0                     {theta};")
edit(tp, r"^waterOnlyPatches \(inlet\);\n", "waterOnlyPatches (inlet);\n\n// change L (of9-port 8a97d02)\nporousFreeAirKrPorous on;\n")
cd = f"{name}/system/controlDict"
edit(cd, r"^endTime\s+[^;]+;", "endTime         3e-3;")
print(f"{name}: K {K} on {n} cells, pc0 {pc0}, m {m}, theta {theta}")
PYEOF
done
