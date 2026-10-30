#!/bin/bash
# Builds the screening runs of this study (README.md) from the truncated REV of study 2c, run T11 (first 0.7 mm of
# the REV_lowpc mesh and initial fields, built there by makeREVcut.sh; K 1e-11, pc0 1000, m 0.4, theta 40, no L).
#     ./makeCases.sh [run ...]       (no argument: all runs of the table below; an existing run folder is replaced)
# Per run: name, yarn K [m2], pc0 [Pa], m, theta0 [deg], then optional ("-" = default): height [m] of the initial gap water
# column (free box cells; default the 0.1 mm of T11), cut height [m] (default the 0.7 mm of T11; else cut here from the full
# mesh FULL, the Allpre output of REV_lowpc, as makeREVcut.sh), minimum initial yarn saturation.
# All runs: porousFreeAirKrPorous on, 3 ms, writes every 0.1 ms.
cd "${0%/*}" || exit 1
PY=${PY:-../../.venv/bin/python}
SRC=${SRC:-../study2c_nearSaturation/T11_cut_lowpc_t40}
FULL=${FULL:-$HOME/PDM_results/REV_lowpc_run3059}

RUNS="
S1_K1e-12_t40       1e-12 5000 0.5 40
S2_K1e-12_t30       1e-12 5000 0.5 30
S3_K1e-12_lowpc_t40 1e-12 1000 0.4 40
S4_K1e-12_t20       1e-12 5000 0.5 20
S5_K1e-12_t40_fill33 1e-12 5000 0.5 40 3.3e-4
S6_C_wet_cut12      2e-11 500 0.4 40 - 1.2e-3 0.9
"

[ -f "$SRC/constant/polyMesh/owner" ] && [ -f "$SRC/0/K" ] || { echo "no mesh or 0/K in $SRC"; exit 1; }
want=" $* "
echo "$RUNS" | while read -r name K pc0 m theta fill ycut sw; do
    [ -n "$name" ] || continue
    [ $# -eq 0 ] || [[ "$want" == *" $name "* ]] || continue
    case "$name" in S[0-9]*) ;; *) echo "bad run name $name"; exit 1 ;; esac
    rm -rf "./$name"
    mkdir "./$name"
    if [ -n "$ycut" ] && [ "$ycut" != "-" ]; then
        cp -r "$FULL/0" "$FULL/constant" "$FULL/system" "$FULL/caseSetup" "./$name/"
        rm -rf "./$name/constant/polyMesh/sets" "./$name/constant/triSurface"
        cat > "./$name/system/topoSetDict" <<EOT
FoamFile { version 2.0; format ascii; class dictionary; object topoSetDict; }
actions
(
    { name keep; type cellSet; action new; source boxToCell; sourceInfo { box (-1 -1 -1) (1 $ycut 1); } }
);
EOT
        ( cd "./$name" && topoSet > log.topoSet 2>&1 && subsetMesh keep -overwrite -patch outlet > log.subsetMesh 2>&1 ) \
            || { echo "$name: topoSet/subsetMesh failed"; exit 1; }
        rm -rf "./$name/constant/polyMesh/sets"
    else
        cp -r "$SRC/0" "$SRC/constant" "$SRC/system" "$SRC/caseSetup" "./$name/"
    fi
    "$PY" - "$name" "$K" "$pc0" "$m" "$theta" "${fill:--}" "${ycut:--}" "${sw:--}" <<'PYEOF'
import re, sys
name, K, pc0, m, theta, fill, ycut, sw = sys.argv[1:9]


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
if float(K) >= 2e-11:  # porous/free faces at Da ~0.1 with K 2e-11, as REV_gapflow
    edit(tp, r"^darcyFaceMaxDa\s+[^;]+;", "darcyFaceMaxDa  0.2;")
cd = f"{name}/system/controlDict"
edit(cd, r"^endTime\s+[^;]+;", "endTime         3e-3;")
if ycut != "-":  # the settings makeREVcut.sh gave T11
    edit(cd, r"^writeInterval\s+[^;]+;[^\n]*", "writeInterval   1e-04;")
    edit(cd, r'^(    waterBudget   \{ #include "\.\./\.\./tools/waterBudget" \}\n)',
         r'\1    dsLocator     { #include "../../tools/dsLocator" }\n')
    edit(f"{name}/caseSetup", r"^N\s+\d+;", "N 4;")
def values(path):
    L = open(path).read().split("\n")
    i = next(k for k, l in enumerate(L) if l.startswith("internalField"))
    n = int(L[i + 1])
    assert L[i + 2] == "("
    return L, i + 3, n


if fill != "-" or sw != "-":
    LC, iC, nC = values(f"{name}/0/C")
    La, ia, na = values(f"{name}/0/alpha.wetting")
    Le, ie, ne = values(f"{name}/0/eps")
    assert nC == na == ne
    v = open(f"{name}/system/blockMeshDict").read().split("vertices", 1)[1].split(");", 1)[0]
    zv = sorted({float(t.split()[2]) for t in re.findall(r"\(\s*([-\d.e+]+\s+[-\d.e+]+\s+[-\d.e+]+)\s*\)", v)})
    nf = nw = 0
    for k in range(nC):
        x, y, z = map(float, LC[iC + k].strip("()").split())
        porous = float(Le[ie + k]) <= 0.99
        # same rule as initFields.py --free-fill: free cells of the fabric box below the height, full of water
        if fill != "-" and not porous and zv[1] < z < zv[2] and y < float(fill):
            La[ia + k] = "1"
            nf += 1
        if sw != "-" and porous and float(La[ia + k]) < float(sw):
            La[ia + k] = sw
            nw += 1
    open(f"{name}/0/alpha.wetting", "w").write("\n".join(La))
    print(f"{name}: initial gap column to y = {fill} m ({nf} free cells), yarn cells raised to S = {sw}: {nw}")
print(f"{name}: K {K} on {n} cells, pc0 {pc0}, m {m}, theta {theta}")
PYEOF
done
