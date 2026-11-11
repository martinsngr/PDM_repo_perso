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
# Full length (2026-11-11, NA 133: y 0.333-3.0 mm, the domain of job 3068; settings of study 2e's Bbox_full: 30 ms, a
# write every 0.5 ms, 72 h, LOG_EVERY 100, 16G, requeued after a node crash and continued from the last complete write
# with job_restart.slurm; job.slurm and job_restart.slurm from ../study2e_bathLayer/Bbox_full):
#   N2_full    N2_noJfix on the full length: job 3068 with J off and alpha fixedValue 1 on the bath
#   N2c_full   N2_full with the bath faces under the z layers closeZ (comma-separated, z layers of the padded grid: 3
#              padding layers below the box) closed: Allpre moves them from inlet to the patch bathWall (closed: the
#              bathWall entries of 0.orig/U and p, alpha zeroGradient), then rebuilds 0/alpha.wetting with the narrowed
#              inlet, so the initial 0.1 mm water column is not set in those layers (initFields.py fills only across
#              the inlet's extent): no bath under them. 3,16 = the two outermost box layers next to the padding, whose
#              air-rich bath-surface cells carried two thirds of the inflow in N2_noJfix at 3 ms (README, Results)
#     ./makeCases.sh [name ...]          (no name: every case)
set -e
cd "${0%/*}"
SRC=../study2e_bathLayer/R0_inlet
FULL=../study2e_bathLayer/Bbox_full
#        name       job     J    alphaInlet  NA   N   closeZ
specs=( "R0_J       2gR0    on   inletOutlet 58   4   -"
        "N1_noJ     2gN1    off  inletOutlet 58   4   -"
        "N2_noJfix  2gN2    off  fixedValue  58   4   -"
        "N2_full    2gN2F   off  fixedValue  133  8   -"
        "N2c_full   2gN2cF  off  fixedValue  133  8   3,16" )
only=" $* "
for spec in "${specs[@]}"; do
    read -r name job J ain NA N closeZ <<< "$spec"
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

    if [ "$NA" -eq 58 ]; then
        what="= R0_inlet of study 2e: job 3068 cut at y 1.496 mm"
    else
        what="y 0.333-3.0 mm: the domain of job 3068"
    fi
    cat > "$name/Allpre" <<EOT
#!/bin/bash
cd "\${0%/*}" || exit 1
# Mesh and initial fields of $name (study 2g, ../README.md): ../../study2e_bathLayer/buildCase.sh with NB = 0 rows of
# bath layer below the bath plane and NA = $NA fabric rows above it ($what).
./clean
../../study2e_bathLayer/buildCase.sh . 0 $NA
EOT
    if [ "$closeZ" != - ]; then
        cat >> "$name/Allpre" <<EOT
# study 2g, $name: the bath faces under the z layers CLOSE_Z of the fabric box (z layers of the padded grid, 3 padding
# layers below the box) are closed: moved from the patch inlet to bathWall (closed walls in 0.orig/U and p: noSlip,
# fixedFluxPressure; alpha zeroGradient). Then 0/alpha.wetting is rebuilt by initFields.py with the narrowed inlet (the
# options of ../../study2e_bathLayer/buildCase.sh plus the closed bathWall): the initial 0.1 mm water column is set only
# across the inlet's extent, so those layers start dry (no bath under them). createPatch works on the mesh only: the
# fields of 0/ that name their patches one by one (eps, K, fYarn, yarnID) get a bathWall entry (zeroGradient).
CLOSE_Z="${closeZ//,/ }"
EOT
        cat >> "$name/Allpre" <<'EOT'
PY=${PY:-../../../.venv/bin/python}
[ -x "$PY" ] || PY=python3
. "$WM_PROJECT_DIR/bin/tools/RunFunctions"
[ -f constant/polyMesh/owner ] && [ -f 0/alpha.wetting ] || { echo "ERROR: buildCase.sh did not build the case."; exit 1; }
rm -f log.topoSet.closeBath log.createPatch.closeBath log.checkMesh.closeBath log.postProcess.closeBath \
      log.initFields.closeBath
"$PY" - $CLOSE_Z <<'PYEOF' || exit 1
import re, sys
layers = [int(k) for k in sys.argv[1:]]
v = open("system/blockMeshDict").read()
pts = [tuple(map(float, t.split())) for t in re.findall(r"\(\s*([-\d.e+]+\s+[-\d.e+]+\s+[-\d.e+]+)\s*\)",
                                                         v.split("vertices", 1)[1].split(");", 1)[0])]
y0 = min(p[1] for p in pts)                                   # the bath plane (inlet)
z = sorted({p[2] for p in pts})                               # padding, box, box, padding
npad = int(re.findall(r"hex \(0 1 2 3 4 5 6 7\) \(\d+ \d+ (\d+)\)", v)[0])
nbox = int(re.findall(r"hex \(4 5 6 7 8 9 10 11\) \(\d+ \d+ (\d+)\)", v)[0])
dz = (z[2] - z[1]) / nbox
boxes = []
for k in layers:
    b = k - npad
    assert 0 <= b < nbox, f"z layer {k} is not a layer of the fabric box ({npad} to {npad + nbox - 1})"
    # face centres of layer k on the plane y0: z = z[1] + (b + 0.5) dz
    boxes.append(f"(-1 {y0 - dz / 4:.9g} {z[1] + (b + 0.25) * dz:.9g}) (1 {y0 + dz / 4:.9g} {z[1] + (b + 0.75) * dz:.9g})")
    print(f"closeBath: z layer {k} (box layer {b}): z {z[1] + b * dz:.6g} to {z[1] + (b + 1) * dz:.6g} m, y0 {y0:.6g} m")
open("system/topoSetDict", "w").write(
    "FoamFile { version 2.0; format ascii; class dictionary; object topoSetDict; }\nactions\n(\n"
    f"    {{ name closeBath; type faceSet; action new;    source boxToFace;   sourceInfo {{ boxes ({' '.join(boxes)}); }} }}\n"
    "    { name closeBath; type faceSet; action subset; source patchToFace; sourceInfo { name inlet; } }\n);\n")
open("system/createPatchDict", "w").write(
    "FoamFile { version 2.0; format ascii; class dictionary; object createPatchDict; }\npointSync false;\npatches\n(\n"
    "    { name bathWall; patchInfo { type patch; } constructFrom set; set closeBath; }\n);\n")
PYEOF
runApplication -s closeBath topoSet || exit 1
runApplication -s closeBath createPatch -overwrite || exit 1
rm -rf constant/polyMesh/sets
runApplication -s closeBath checkMesh || exit 1
"$PY" - $CLOSE_Z <<'PYEOF' || exit 1
import os, re, sys
import numpy as np
def strip(t):
    return re.sub(r"FoamFile\s*\{.*?\}", "", re.sub(r"/\*.*?\*/", "", t, flags=re.S), count=1, flags=re.S)
b = open("constant/polyMesh/boundary").read()
pat = {m.group(1): (int(m.group(2)), int(m.group(3)))
       for m in re.finditer(r"\n\s*(\w+)\s*\{[^}]*?nFaces\s+(\d+);[^}]*?startFace\s+(\d+);", b)}
nx = int(re.findall(r"hex \(4 5 6 7 8 9 10 11\) \((\d+) \d+ \d+\)", open("system/blockMeshDict").read())[0])
nw, sw = pat["bathWall"]
assert nw == nx * (len(sys.argv) - 1), f"bathWall has {nw} faces, expected {nx} per closed layer"
own = np.array(strip(open("constant/polyMesh/owner").read()).split("(", 1)[1].split(")", 1)[0].split(), int)
eb = open("0/eps").read().split("internalField", 1)[1]
ne = int(re.search(r"(\d+)\s*\(", eb).group(1))
eps = np.array(eb.split("(", 1)[1].split(")", 1)[0].split()[:ne], float)
assert (eps[own[sw:sw + nw]] > 0.99).all(), "a closed bath face lies under a yarn cell"
ni, si = pat["inlet"]
ein = eps[own[si:si + ni]]
print(f"closeBath: bathWall {nw} faces (all free cells); inlet {ni} faces ({(ein <= 0.99).sum()} porous, "
      f"{(ein > 0.99).sum()} free)")
entry = "    bathWall\n    {\n        type zeroGradient;\n    }\n"
for f in sorted(os.listdir("0")):
    s = open(os.path.join("0", f)).read()
    if f == "alpha.wetting" or "bathWall" in s or '".*"' in s:
        continue
    m = re.search(r"\n    inletPad\n    \{\n.*?\n    \}\n", s, re.S)
    assert m, f"0/{f}: no inletPad entry to put bathWall next to"
    open(os.path.join("0", f), "w").write(s[:m.end()] + entry + s[m.end():])
    print(f"closeBath: 0/{f}: bathWall entry added (zeroGradient)")
PYEOF
runApplication -s closeBath postProcess -func writeCellCentres -time 0 || exit 1
"$PY" ../../../meshing_strat_trial/tools/initFields.py --closed-patch outlet --closed-patch inletPad --closed-patch bathWall \
    --free-fill 1e-4 --sat-height 1e-4 --porous-in 1 > log.initFields.closeBath 2>&1 || { cat log.initFields.closeBath; exit 1; }
cat log.initFields.closeBath
rm -f 0/C 0/Cx 0/Cy 0/Cz
EOT
    fi
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

    if [ "$NA" -eq 58 ]; then
    sed -e "s/--job-name=2eR0/--job-name=$job/" -e "s/--mem=16G/--mem=8G/" \
        -e "s#chmod +x Allpre run clean \.\./buildCase\.sh#chmod +x Allpre run clean ../../study2e_bathLayer/buildCase.sh#" \
        -e "s#^\# SLURM job of R0_inlet (study 2e, \.\./README\.md)#\# SLURM job of $name (study 2g, ../README.md; built as R0_inlet of study 2e)#" \
        "$SRC/job.slurm" > "$name/job.slurm"
    grep -q "job-name=$job" "$name/job.slurm" && grep -q "study2e_bathLayer/buildCase.sh" "$name/job.slurm" \
        && grep -q "study 2g" "$name/job.slurm"
    else
        # full length: the run settings of Bbox_full (30 ms, writes every 0.5 ms, 72 h, LOG_EVERY 100, 16G, continued after
        # a node crash by job_restart.slurm); N cores from the table
        ../../.venv/bin/python - "$name/system/controlDict" "$name" <<'PYEOF'
import re, sys
p, name = sys.argv[1:3]
s = open(p).read()
def sub(pat, new):
    global s
    s, n = re.subn(pat, new, s, flags=re.M)
    assert n == 1, pat
sub(r"^// study 2e \(2026-11-03\): R0_inlet, .*$",
    f"// study 2g (2026-11-11): {name}, y 0.333-3.0 mm (0 rows of bath layer, the domain of job 3068), 0.03 s")
sub(r"^endTime\s+[^;]+;", "endTime         0.03;")
sub(r"^writeInterval\s+[^;]+;", "writeInterval   5e-04;")
open(p, "w").write(s)
PYEOF
        sed -i "s#^N .*#N $N;   // study 2g: set by ../makeCases.sh#" "$name/caseSetup"
        grep -q "^N $N;" "$name/caseSetup"
        sed -e "s/--job-name=2eBboxF/--job-name=$job/" -e "s/--ntasks=16/--ntasks=$N/" -e "s/ on 16 cores\./ on $N cores./" \
            -e "s#chmod +x Allpre run clean \.\./buildCase\.sh#chmod +x Allpre run clean ../../study2e_bathLayer/buildCase.sh#" \
            -e "s#^\# SLURM job of Bbox_full (study 2e, \.\./README\.md)#\# SLURM job of $name (study 2g, ../README.md; run settings of Bbox_full, study 2e)#" \
            "$FULL/job.slurm" > "$name/job.slurm"
        sed -e "s/--job-name=2eBboxF/--job-name=$job/" -e "s/--ntasks=16/--ntasks=$N/" \
            -e "s#restarting the study 2e run Bbox_full#restarting the study 2g run $name#" \
            "$FULL/job_restart.slurm" > "$name/job_restart.slurm"
        chmod +x "$name/job_restart.slurm"
        for f in job.slurm job_restart.slurm; do
            grep -q "job-name=$job" "$name/$f" && grep -q "ntasks=$N\$" "$name/$f" && grep -q "study 2g" "$name/$f"
        done
        grep -q "study2e_bathLayer/buildCase.sh" "$name/job.slurm" && grep -q "exec bash job_restart.slurm" "$name/job.slurm"
        grep -q "^\. \.\./\.\./\.\./meshing_strat_trial/tools/runTools\.sh" "$name/job_restart.slurm"
    fi
    msg=""
    [ "$closeZ" != - ] && msg=", bath closed under z layers $closeZ"
    echo "$name: written (J $J, alpha inlet $ain, NA $NA, $N cores$msg)"
done
