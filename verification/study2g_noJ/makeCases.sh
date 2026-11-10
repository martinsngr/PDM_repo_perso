#!/bin/bash
# makeCases.sh  -  writes the study 2g cases (README.md) from ../study2e_bathLayer/R0_inlet (job 3068 cut at y 1.496 mm:
# the first 58 fabric rows above the mid-gap bath plane; built and smoke-tested 2026-11-03, never run). The mesh and 0/
# are built by each case's Allpre (../../study2e_bathLayer/buildCase.sh . 0 58), inside the cluster job.
# Changes from R0_inlet, the same in every case:
#   system/controlDict   function objects included from ../../../study2e_bathLayer/tools (the study 2c copies: scalar K)
#   Allpre, job.slurm    ../buildCase.sh -> ../../study2e_bathLayer/buildCase.sh; job name; memory 8G
# Cases (values of job 3068: scalar K 1e-11, VG 5000 / 0.5, theta 60 deg, G + H + F' + I, L; 3 ms, 4 cores, a write
# every 0.1 ms):
#   R0_J       = R0_inlet: J on the inlet (waterOnlyPatches): the reference, on the same cut and decomposition
#   N1_noJ     waterOnlyPatches removed (constant/transportProperties), BCs unchanged: p totalPressure 0, U
#              pressureInletOutletVelocity, alpha inletOutlet 1 on every inlet face (alpha 1 on inflow, the cell's alpha
#              on outflow): the inlet as before J, with today's BCs and initial state
#   N2_noJfix  as N1_noJ with alpha fixedValue 1 on the inlet (Allpre rewrites the inlet entry of 0/alpha.wetting after
#              initFields.py): every inlet face flux booked as water, as J does, but no face closure and air mobility
#              on the yarn faces of the bath
#     ./makeCases.sh [name ...]          (no name: every case)
set -e
cd "${0%/*}"
SRC=../study2e_bathLayer/R0_inlet
#        name       job   J    alphaInlet
specs=( "R0_J       2gR0  on   inletOutlet"
        "N1_noJ     2gN1  off  inletOutlet"
        "N2_noJfix  2gN2  off  fixedValue" )
only=" $* "
for spec in "${specs[@]}"; do
    read -r name job J ain <<< "$spec"
    [ $# -gt 0 ] && [[ "$only" != *" $name "* ]] && continue
    rm -rf "$name"
    mkdir -p "$name/constant" "$name/system"
    cp -r "$SRC/0.orig" "$name/"
    cp "$SRC"/constant/{dynamicMeshDict,g,momentumTransport,transportProperties} "$name/constant/"
    cp "$SRC"/system/{controlDict,fvSchemes,fvSolution,decomposeParDict} "$name/system/"
    cp "$SRC"/{caseSetup,clean,run} "$name/"
    touch "$name/$name.foam"
    sed -i 's#"\.\./\.\./tools/#"../../../study2e_bathLayer/tools/#; s#(\.\./\.\./tools/stopGuard)#(../../../study2e_bathLayer/tools/stopGuard)#' \
        "$name/system/controlDict"
    [ "$(grep -c 'study2e_bathLayer/tools/' "$name/system/controlDict")" -ge 5 ]

    cat > "$name/Allpre" <<EOT
#!/bin/bash
cd "\${0%/*}" || exit 1
# Mesh and initial fields of $name (study 2g, ../README.md): ../../study2e_bathLayer/buildCase.sh with NB = 0 rows of
# bath layer below the bath plane and NA = 58 fabric rows above it (= R0_inlet of study 2e: job 3068 cut at y 1.496 mm).
./clean
../../study2e_bathLayer/buildCase.sh . 0 58
EOT
    if [ "$ain" = fixedValue ]; then
        cat >> "$name/Allpre" <<'EOT'
# study 2g, N2_noJfix: alpha fixedValue 1 on every inlet face (initFields.py writes inletOutlet 1)
PY=${PY:-../../../.venv/bin/python}
[ -x "$PY" ] || PY=python3
"$PY" - <<'PYEOF'
import re
p = "0/alpha.wetting"
s = open(p).read()
head, bf = s.split("boundaryField", 1)
new, n = re.subn(r"\n    inlet\n    \{\n.*?\n    \}\n",
                 "\n    inlet\n    {\n        type fixedValue;\n        value uniform 1;\n    }\n", bf, count=1, flags=re.S)
assert n == 1, "inlet entry of 0/alpha.wetting not found"
open(p, "w").write(head + "boundaryField" + new)
print("0/alpha.wetting: inlet fixedValue 1")
PYEOF
EOT
    fi
    chmod +x "$name/Allpre"

    if [ "$J" = off ]; then
        ../../.venv/bin/python - "$name/constant/transportProperties" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p).read()
i = s.index("// Reservoir (inlet) that exchanges water only")
j = s.index("waterOnlyPatches (inlet);\n") + len("waterOnlyPatches (inlet);\n")
new = ("// Study 2g (../README.md): change J off, no waterOnlyPatches. The inlet is the plain\n"
       "// boundary of 0/: alpha flux alpha_b*phi_b on every face (inletOutlet: alpha_b 1 on\n"
       "// inflow, the cell's alpha on outflow; N2_noJfix: fixedValue 1), air mobility on the\n"
       "// yarn faces, no face closure. R0_J keeps J.\n")
open(p, "w").write(s[:i] + new + s[j:])
PYEOF
        ! grep -q "^waterOnlyPatches" "$name/constant/transportProperties"
        # the run must stop if the binary reports J active (keyword left somewhere)
        ../../.venv/bin/python - "$name/run" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p).read()
anchor = "runApplication decomposePar\n"
guard = ("# study 2g: J must be off in this case\n"
         "if grep -q \"^waterOnlyPatches:\" log.hybridPorousInterFoam.precompile; then\n"
         "    echo \"ERROR: J is active (waterOnlyPatches) in a no-J case of study 2g.\"\n"
         "    exit 1\n"
         "fi\n")
assert s.count(anchor) == 1
open(p, "w").write(s.replace(anchor, guard + anchor))
PYEOF
    fi
    chmod +x "$name/run" "$name/clean"

    sed -e "s/--job-name=2eR0/--job-name=$job/" -e "s/--mem=16G/--mem=8G/" \
        -e "s#chmod +x Allpre run clean \.\./buildCase\.sh#chmod +x Allpre run clean ../../study2e_bathLayer/buildCase.sh#" \
        -e "s#^\# SLURM job of R0_inlet (study 2e, \.\./README\.md)#\# SLURM job of $name (study 2g, ../README.md; built as R0_inlet of study 2e)#" \
        "$SRC/job.slurm" > "$name/job.slurm"
    grep -q "job-name=$job" "$name/job.slurm" && grep -q "study2e_bathLayer/buildCase.sh" "$name/job.slurm" \
        && grep -q "study 2g" "$name/job.slurm"
    echo "$name: written (J $J, alpha inlet $ain)"
done
