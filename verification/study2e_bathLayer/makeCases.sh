#!/bin/bash
# makeCases.sh  -  writes the dictionaries and scripts of the study 2e cases (README.md) from
# ../../meshing_strat_trial/REV_midbath (job 3068). The mesh and 0/ are built by each case's Allpre (buildCase.sh),
# inside the cluster job. Changes from REV_midbath, the same in every case:
#   0.orig/U, 0.orig/p     the closed-wall entry also matches bathWall (the cases with a bath layer have that patch)
#   system/controlDict     endTime, writeInterval (table below), function object dsLocator (../tools = study 2c copies)
#   caseSetup              N (table below)
#   run, job_restart.slurm ../tools/runTools.sh -> ../../../meshing_strat_trial/tools/runTools.sh
#   constant/              unchanged (K 1e-11, VG 5000 / 0.5, theta 60 deg, G + H + F' + I, J on inlet, L)
# Cases (NB rows of bath layer below the plane y0, NA fabric rows above it):
#   B_full    NB 5, NA 133 (y 0.233-3.0 mm, the length of job 3068): 30 ms, 16 cores, writes every 0.5 ms as job 3068,
#             requeued after a node crash and continued from the last complete write (job_restart.slurm). The run.
#   R0_inlet  NB 0, NA 58  (y 0.333-1.496 mm): job 3068 cut, 3 ms, 4 cores, writes every 0.1 ms
#   B_layer   NB 5, NA 58: R0_inlet with the bath layer, 3 ms, 4 cores, writes every 0.1 ms
#             (R0_inlet and B_layer: short variants for diagnostics, built and smoke-tested, not submitted: the user runs
#             B_full only, 2026-11-03)
#   Bbox_cut  as B_layer with the bath under the fabric box only (mode box: the layer cells under the padding removed,
#             padding floor closed at y0), 3 ms, 4 cores: the leak test of option 1 (2026-11-04; B_full, job 3072, leaked
#             through the open padding beside its bath)
#   Bbox_full as B_full in mode box, 30 ms, 16 cores, requeued and continued like B_full: run after Bbox_cut passes
#     ./makeCases.sh
set -e
cd "${0%/*}"
SRC=../../meshing_strat_trial/REV_midbath
#        name      NB  NA   job       N  endTime writeInterval hours logEvery restart mode
specs=( "R0_inlet  0   58   2eR0      4  3e-3    1e-04         12    20       no      -"
        "B_layer   5   58   2eB       4  3e-3    1e-04         12    20       no      -"
        "B_full    5   133  2eBfull   16 0.03    5e-04         72    100      yes     -"
        "Bbox_cut  5   58   2eBboxC   4  3e-3    1e-04         12    20       no      box"
        "Bbox_full 5   133  2eBboxF   16 0.03    5e-04         72    100      yes     box" )
for spec in "${specs[@]}"; do
    read -r name NB NA job N endTime wInt hours logEvery restart mode <<< "$spec"
    [ "$mode" = - ] && mode=""
    rm -rf "$name"
    mkdir -p "$name/0.orig" "$name/constant" "$name/system"
    cp "$SRC"/0.orig/{U,UnonWetting,Uwetting,p} "$name/0.orig/"
    cp "$SRC"/constant/{dynamicMeshDict,g,momentumTransport,transportProperties} "$name/constant/"
    cp "$SRC"/system/{controlDict,fvSchemes,fvSolution,decomposeParDict} "$name/system/"
    cp "$SRC"/{caseSetup,clean} "$name/"
    touch "$name/$name.foam"
    sed 's/^\(\s*\)"(outlet|inletPad)"/\1"(outlet|inletPad|bathWall)"/' -i "$name/0.orig/U" "$name/0.orig/p"
    grep -q 'outlet|inletPad|bathWall' "$name/0.orig/U" && grep -q 'outlet|inletPad|bathWall' "$name/0.orig/p"
    sed "s#^N .*;#N $N;   // study 2e: set by ../makeCases.sh#" -i "$name/caseSetup"
    grep -q "^N $N;" "$name/caseSetup"
    sed 's#^\. \.\./tools/runTools\.sh#. ../../../meshing_strat_trial/tools/runTools.sh#' "$SRC/run" > "$name/run"
    grep -q 'meshing_strat_trial/tools/runTools.sh' "$name/run"
    ylo=$([ "$NB" -gt 0 ] && echo 0.233 || echo 0.333); yhi=$([ "$NA" -eq 133 ] && echo 3.0 || echo 1.496)
    ../../.venv/bin/python - "$name/system/controlDict" "$endTime" "$wInt" \
        "// study 2e (2026-11-03): $name, y $ylo-$yhi mm ($NB rows of bath layer${mode:+ under the fabric box only}), $endTime s" <<'PYEOF'
import re, sys
p, end, wint, comment = sys.argv[1:5]
s = open(p).read()
def sub(pat, new):
    global s
    s, n = re.subn(pat, new, s, flags=re.M)
    assert n == 1, pat
sub(r"^// REV_midbath \(2026-11-02\).*\n.*\n", comment + "\n")
sub(r"^endTime\s+[^;]+;", f"endTime         {end};")
sub(r"^writeInterval\s+[^;]+;[^\n]*", f"writeInterval   {wint};")
sub(r'^(    waterBudget   \{ #include "\.\./\.\./tools/waterBudget" \}\n)',
    r'\1    dsLocator     { #include "../../tools/dsLocator" }\n')
open(p, "w").write(s)
PYEOF
    cat > "$name/Allpre" <<EOT
#!/bin/bash
cd "\${0%/*}" || exit 1
# Mesh and initial fields of $name (study 2e, ../README.md): ../buildCase.sh with NB = $NB rows of bath layer
# below the bath plane and NA = $NA fabric rows above it${mode:+, mode $mode (bath under the fabric box only)}.
./clean
../buildCase.sh . $NB $NA${mode:+ $mode}
EOT
    if [ "$restart" = yes ]; then
        requeue="#SBATCH --open-mode=append
# After a node crash SLURM may requeue the job (seen 2026-10-30): it then continues from the last complete write (below)."
        resume='# requeued after a crash (or submitted again on a run in progress): continue it, never rerun ./Allpre, which deletes the
# results; ./clean first for a fresh start
if [ -d processor0 ]; then
    echo "processor0 exists: continuing with job_restart.slurm"
    exec bash job_restart.slurm
fi'
        sed -e "s#^\. \.\./tools/runTools\.sh#. ../../../meshing_strat_trial/tools/runTools.sh#" \
            -e "s#^\#SBATCH --job-name=.*#\#SBATCH --job-name=$job#" \
            -e "s#^\#SBATCH --ntasks=.*#\#SBATCH --ntasks=$N#" \
            -e "s#restarting the REV_midbath run#restarting the study 2e run $name#" \
            -e "s#LOG_EVERY=100#LOG_EVERY=$logEvery#" \
            "$SRC/job_restart.slurm" > "$name/job_restart.slurm"
        grep -q 'meshing_strat_trial/tools/runTools.sh' "$name/job_restart.slurm"
        grep -q "study 2e run $name" "$name/job_restart.slurm"
        chmod +x "$name/job_restart.slurm"
        crash="Requeued after a node crash: continues from the last complete write (job_restart.slurm)."
    else
        requeue="#SBATCH --no-requeue"
        resume=""
        crash="Not requeued after a node crash (a requeue would rerun Allpre): resubmit by hand."
    fi
    cat > "$name/job.slurm" <<EOT
#!/bin/bash
# SLURM job of $name (study 2e, ../README.md) on mini03: builds the case (./Allpre: mesh, fields, ~1 min with embreex),
# then runs it to $endTime s on $N cores. Needs the repo .venv (numpy, scipy, trimesh==5.1.0, rtree, embreex) and the
# solver of9-port 8a97d02 or later. Submit from this folder: sbatch job.slurm. $crash
#SBATCH --job-name=$job
#SBATCH --partition=global
#SBATCH --nodes=1
#SBATCH --ntasks=$N
#SBATCH --mem=16G
#SBATCH --time=$hours:00:00
$requeue
#SBATCH --output=Log_%x_%j.log
#SBATCH --error=Err_%x_%j.err
#SBATCH --mail-user=martin.sinegre@gmail.com
#SBATCH --mail-type=END,FAIL

# OpenFOAM 9 environment (sourced before set -e: the bashrc may return non-zero)
source /opt/OpenFOAM-9/etc/bashrc

set -e
cd "\${SLURM_SUBMIT_DIR}"
echo "Job ID: \${SLURM_JOB_ID}  Host: \$(hostname)  Directory: \$(pwd)"
echo "Allocated tasks: \${SLURM_NTASKS}  Solver: \$(which hybridPorousInterFoam)  Start: \$(date)"

$resume
N=\$(foamDictionary -entry N -value caseSetup)
if [ "\$N" -ne "\${SLURM_NTASKS}" ]; then
    echo "ERROR: N = \$N in caseSetup but --ntasks = \${SLURM_NTASKS}"
    exit 1
fi
if ! ../../../.venv/bin/python -c "import numpy, trimesh, rtree" 2>/dev/null; then
    echo "ERROR: no repo .venv with numpy, trimesh and rtree."
    exit 1
fi
chmod +x Allpre run clean ../buildCase.sh
./Allpre
LOG_DIR=logs LOG_EVERY=$logEvery ./run
echo "End: \$(date)"
EOT
    chmod +x "$name/Allpre" "$name/run" "$name/clean"
    echo "$name written (NB $NB, NA $NA, $N cores, endTime $endTime, job $job, restart $restart)"
done
