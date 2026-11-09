#!/bin/bash
# ON HOLD (2026-11-09): the laptop smoke test fails at 31 us (air leaks into the bath and cannot leave; ../../README.md,
# horizontal). Do not submit before that is solved: the job stops here.
echo "horizontal is on hold (../../README.md): not submitted"; exit 1
# SLURM job of horizontal (REV_pipeline, ../../README.md): the fabric lying flat on a bath at rest, water rising through
# the thickness (the previous student's set-up), REV values with theta 40 deg, gravity -z, x and y cyclic; 5 ms.
# The job builds the case itself (./Allpre: mesh, eps/K, initial alpha) from the pulled repo, then runs it.
# Needs on the cluster: the repo .venv with numpy, scipy, trimesh==5.1.0, rtree, embreex (at the repo root) and the
# solver of9-port 8a97d02 or later (4bb5d2e installed).
# Submit from this folder with sbatch job.slurm after checking the load with squeue; never ./run there.
#SBATCH --job-name=REVhoriz
#SBATCH --partition=global
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --mem=16G
#SBATCH --open-mode=append
#SBATCH --time=72:00:00
# (estimate: see ../../README.md, from the laptop smoke test)
# After a node crash SLURM may requeue the job (seen 2026-10-30): it then continues from the last complete write (below).
#SBATCH --output=Log_%x_%j.log
#SBATCH --error=Err_%x_%j.err
#SBATCH --mail-user=martin.sinegre@gmail.com
#SBATCH --mail-type=END,FAIL

# OpenFOAM 9 environment (sourced before set -e: the bashrc may return non-zero)
source /opt/OpenFOAM-9/etc/bashrc

set -e
cd "${SLURM_SUBMIT_DIR}"

echo "Job ID: ${SLURM_JOB_ID}  Host: $(hostname)  Directory: $(pwd)"
echo "Allocated tasks: ${SLURM_NTASKS}  Solver: $(which hybridPorousInterFoam)  Start: $(date)"

# requeued after a crash (or submitted again on a run in progress): continue it, never rerun ./Allpre, which deletes the
# results; ./clean first for a fresh start
if [ -d processor0 ]; then
    echo "processor0 exists: continuing with job_restart.slurm"
    exec bash job_restart.slurm
fi

N=$(foamDictionary -entry N -value caseSetup)
if [ "$N" -ne "${SLURM_NTASKS}" ]; then
    echo "ERROR: N = $N in caseSetup but --ntasks = ${SLURM_NTASKS}"
    exit 1
fi
if ! ../../../.venv/bin/python -c "import numpy, trimesh, rtree" 2>/dev/null; then
    echo "ERROR: no repo .venv with numpy, trimesh and rtree (see the top of this file)."
    exit 1
fi

chmod +x Allpre run clean
# mesh and initial fields from the repo scripts (~20 s); the counts must match the laptop build
# (porous 78,528, free 211,944, 290,472 cells: the REV box + 5 bath rows + 5 air rows, laptop build 2026-11-09)
./Allpre
grep -q "porous 78,528, free 211,944" log.initFields || { echo "ERROR: mesh differs from the laptop build"; exit 1; }
# solver log in ./logs during the run (not the node /tmp), filtered at the end to every 100th step + the
# last 400 lines (../../tools/runTools.sh)
LOG_DIR=logs LOG_EVERY=100 ./run

echo "End: $(date)"
