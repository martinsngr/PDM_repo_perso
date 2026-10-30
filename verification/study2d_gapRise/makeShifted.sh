#!/bin/bash
# Builds the runs with the bath plane in the middle of a gap (README.md, S10, S11): the REV_lowpc mesh (FULL) cut to y 0.333-1.5 mm. topoSet + subsetMesh twice: the
# faces at y 0.333 mm join the `inlet` patch (bath, water only: the free faces next to air stay closed), those at y 1.5 mm the closed `outlet`. Initial fields as REV (initFields.py).
#     ./makeShifted.sh <name> <K> <pc0> <m> <theta>
set -e
cd "${0%/*}"
PY=${PY:-../../.venv/bin/python}
FULL=${FULL:-$HOME/PDM_results/REV_lowpc_run3059}
name=$1; K=$2; pc0=$3; m=$4; theta=$5
rm -rf "./$name"; mkdir "./$name"
cp -r "$FULL/0" "$FULL/constant" "$FULL/system" "$FULL/caseSetup" "./$name/"
rm -rf "./$name/constant/polyMesh/sets" "./$name/constant/triSurface"
cut() {  # cut <ylo> <yhi> <patch>
    cat > "./$name/system/topoSetDict" <<EOT
FoamFile { version 2.0; format ascii; class dictionary; object topoSetDict; }
actions
(
    { name keep; type cellSet; action new; source boxToCell; sourceInfo { box (-1 $1 -1) (1 $2 1); } }
);
EOT
    ( cd "./$name" && topoSet > log.topoSet 2>&1 && subsetMesh keep -overwrite -patch "$3" > log.subsetMesh 2>&1 )
    rm -rf "./$name/constant/polyMesh/sets"
}
cut 3.33e-4 1 inlet
cut -1 1.5e-3 outlet
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
if float(K) >= 2e-11:
    edit(tp, r"^darcyFaceMaxDa\s+[^;]+;", "darcyFaceMaxDa  0.2;")
cd = f"{name}/system/controlDict"
edit(cd, r"^endTime\s+[^;]+;", "endTime         3e-3;")
edit(cd, r"^writeInterval\s+[^;]+;[^\n]*", "writeInterval   1e-04;")
edit(cd, r'^(    waterBudget   \{ #include "\.\./\.\./tools/waterBudget" \}\n)', r'\1    dsLocator     { #include "../../tools/dsLocator" }\n')
edit(f"{name}/caseSetup", r"^N\s+\d+;", "N 4;")
PYEOF
# initial alpha from the new bath plane, as REV/Allpre (the free column stays in the fabric box)
cd "./$name"
rm -f 0/C 0/Cx 0/Cy 0/Cz
postProcess -func writeCellCentres -time 0 > log.writeCellCentres 2>&1
"../$PY" ../../../meshing_strat_trial/tools/initFields.py --closed-patch outlet --closed-patch inletPad --free-fill 1e-4 --sat-height 1e-4 --porous-in 1 2>&1 | tail -6
rm -f 0/Cx 0/Cy 0/Cz
# the padding stays air, as in the REV (here its faces at the bath plane belong to `inlet`, so initFields.py fills it): J keeps those faces closed while the cells next to them are air
"../$PY" - <<'PYEOF'
import re
def values(path):
    L = open(path).read().split("\n")
    i = next(k for k, l in enumerate(L) if l.startswith("internalField"))
    n = int(L[i + 1])
    assert L[i + 2] == "("
    return L, i + 3, n
LC, iC, nC = values("0/C")
La, ia, na = values("0/alpha.wetting")
Le, ie, ne = values("0/eps")
v = open("system/blockMeshDict").read().split("vertices", 1)[1].split(");", 1)[0]
zv = sorted({float(t.split()[2]) for t in re.findall(r"\(\s*([-\d.e+]+\s+[-\d.e+]+\s+[-\d.e+]+)\s*\)", v)})
nb = np_ = 0
for k in range(nC):
    if float(Le[ie + k]) > 0.99 and float(La[ia + k]) > 0.5:
        if zv[1] < float(LC[iC + k].strip("()").split()[2]) < zv[2]:
            nb += 1
        else:
            np_ += 1
            La[ia + k] = "0"
open("0/alpha.wetting", "w").write("\n".join(La))
print(f"free water cells: box {nb}, padding {np_} set to air")
PYEOF
