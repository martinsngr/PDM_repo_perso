#!/bin/bash
# Builds the truncated-REV runs of this study (README.md, phase 1c): the REV_lowpc mesh and initial fields cut to the
# first 35 of 133 cell rows along y (y < 0.70 mm). topoSet selects the cells, subsetMesh keeps them and puts the cut
# faces into the closed 'outlet' patch (U noSlip, p fixedFluxPressure, alpha zeroGradient: the REV's closed end).
#     ./makeREVcut.sh [run ...]       (no argument: all runs of the table below)
#     SRC=<case> ./makeREVcut.sh ...  source case: 0/, constant/ (mesh), system/ and caseSetup as written by
#                                     ../../meshing_strat_trial/REV_lowpc/Allpre (default: the copy of job 3059)
# Run each with ./runCut.sh <run ...> (4 cores each, 0.5 ms).
#
# Per run (one line of RUNS): name, pc0 [Pa], m, theta0 [deg], edits (as makeCases.sh: -<kw>, <kw>=<value>; also
# +<kw>=<value>: appends the keyword, for the switches of the scratch solver variants in solver/; end=<s>: end time,
# default 5e-4 s).
cd "${0%/*}" || exit 1
PY=${PY:-../../.venv/bin/python}
SRC=${SRC:-$HOME/PDM_results/REV_lowpc_run3059}
YCUT=7.0e-4      # keep the cells with centre y below this [m]: rows 0-34 (row 34 centre 0.692 mm, row 35 0.712 mm)

RUNS="
T0_cut_lowpc_t60  1000 0.4 60
T1_cut_REVpc_t60  5000 0.5 60
T2_cut_noFp       1000 0.4 60 -porousFreeFluxForce
T3_cut_t90        1000 0.4 90
T4_cut_noG        1000 0.4 60 porousFreeDarcyFaces=off
T5_cut_noH        1000 0.4 60 -porousContactAngleWallLike
T6_cut_noI        1000 0.4 60 -porousFreeNoSlip
T7_cut_K1         1000 0.4 60 +porousFreeKrPorous=on
T8_cut_K2         1000 0.4 60 +porousFreeKrAirPorous=on
T9_cut_G2         1000 0.4 60 +porousFreeVofPc=on
T10_cut_G2b       1000 0.4 60 +porousFreeVofPc=on
T11_cut_lowpc_t40 1000 0.4 40 end=1e-3
T12_cut_t40_K2    1000 0.4 40 +porousFreeKrAirPorous=on,end=2e-3
"

[ -f "$SRC/constant/polyMesh/owner" ] && [ -f "$SRC/0/alpha.wetting" ] || { echo "no mesh or 0/ in $SRC"; exit 1; }
want=" $* "
echo "$RUNS" | while read -r name pc0 m theta edits; do
    [ -n "$name" ] || continue
    [ $# -eq 0 ] || [[ "$want" == *" $name "* ]] || continue
    case "$name" in T[0-9]*) ;; *) echo "bad run name $name"; exit 1 ;; esac
    rm -rf "./$name"
    mkdir "./$name"
    cp -r "$SRC/0" "$SRC/constant" "$SRC/system" "$SRC/caseSetup" "./$name/"
    rm -rf "./$name/constant/polyMesh/sets" "./$name/constant/triSurface"
    cat > "./$name/system/topoSetDict" <<EOT
FoamFile { version 2.0; format ascii; class dictionary; object topoSetDict; }
// study2c phase 1c: cells of the first 0.7 mm along y
actions
(
    { name keep; type cellSet; action new; source boxToCell; sourceInfo { box (-1 -1 -1) (1 $YCUT 1); } }
);
EOT
    ( cd "./$name" && topoSet > log.topoSet 2>&1 && subsetMesh keep -overwrite -patch outlet > log.subsetMesh 2>&1 ) \
        || { echo "$name: topoSet/subsetMesh failed (see $name/log.*)"; exit 1; }
    rm -rf "./$name/constant/polyMesh/sets"
    "$PY" - "$name" "$pc0" "$m" "$theta" "${edits:-}" <<'EOF'
import re, sys
name, pc0, m, theta, edits = sys.argv[1:6]


def edit(path, pattern, new, flags=re.M):
    s = open(path).read()
    s, n = re.subn(pattern, new, s, flags=flags)
    assert n == 1, f"{path}: {pattern!r} matched {n} times"
    open(path, "w").write(s)


tp = f"{name}/constant/transportProperties"
edit(tp, r"^    pc0 pc0 \[1 -1 -2 0 0 0 0\] [^;]+;[^\n]*", f"    pc0 pc0 [1 -1 -2 0 0 0 0] {pc0};")
edit(tp, r"^    m [^;]+;[^\n]*", f"    m {m};")
edit(tp, r"^theta0\s+[^;]+;[^\n]*", f"theta0                     {theta};")
end = "5e-04"
for e in filter(None, edits.split(",")):
    if e.startswith("end="):
        end = e[4:]
    elif e.startswith("+"):
        kw, val = e[1:].split("=", 1)
        s = open(tp).read()
        assert re.search(rf"^{re.escape(kw)}\s", s, re.M) is None, kw
        open(tp, "w").write(s.rstrip("\n").removesuffix("// ************************************************************************* //").rstrip("\n")
                            + f"\n\n// study2c scratch solver variant switch (solver/)\n{kw} {val};\n\n"
                            "// ************************************************************************* //\n")
    elif e.startswith("-"):
        edit(tp, rf"^{re.escape(e[1:])}\s[^\n]*\n", "")
    else:
        kw, val = e.split("=", 1)
        edit(tp, rf"^{re.escape(kw)}\s+[^;]+;", f"{kw} {val};")
cd = f"{name}/system/controlDict"
edit(cd, r"^endTime\s+[^;]+;", f"endTime         {end};")
edit(cd, r"^writeInterval\s+[^;]+;[^\n]*", "writeInterval   1e-04;")
edit(cd, r'^(    waterBudget   \{ #include "\.\./\.\./tools/waterBudget" \}\n)',
     r'\1    dsLocator     { #include "../../tools/dsLocator" }\n')
edit(f"{name}/caseSetup", r"^N\s+\d+;", "N 4;")
b = open(f"{name}/constant/polyMesh/boundary").read()
nf = dict(re.findall(r"\n\s+(\w+)\s*\n\s*\{[^}]*?nFaces\s+(\d+);", b))
cells = int(re.search(r"nCells:\s*(\d+)", open(f"{name}/constant/polyMesh/owner").read()).group(1))
print(f"{name}: pc0 {pc0}, m {m}, theta {theta}, edits [{edits}], {cells} cells, patch faces {nf}")
EOF
done
