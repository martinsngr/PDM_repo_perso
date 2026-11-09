#!/bin/bash
# SLURM job of tensorB (REV_pipeline, ../../README.md): job 3068 (REV values: K 1e-11, Van Genuchten pc0 5000 Pa, m 0.5,
# theta 60 deg, L, bath plane at y 0.333 mm mid-gap, saturated rows) with one change: yarn-aligned diagonal K from Gebart (hex, Vf 0.5, fibre radius 7.5 um): Kpar 4.2e-12, Kperp 9.2e-13, study (b).
# 60 ms: the front moves x0.65 (K x0.42), job 3068's front at 30 ms is reached at ~71 ms; estimate ~12-19 h (dt 3-5x job 3068's) on 8 cores.
# The job builds the case itself (./Allpre: mesh, eps/K, initial alpha) from the pulled repo, then runs it.
# Needs on the cluster: the repo .venv with numpy, scipy, trimesh==5.1.0, rtree, embreex (at the repo root) and the
# solver of9-port 4bb5d2e or later (change T: tensor K).
# Submit from this folder with sbatch job.slurm after checking the load with squeue; never ./run there.
#SBATCH --job-name=REVtensB
#SBATCH --partition=global
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --mem=16G
#SBATCH --open-mode=append
#SBATCH --time=72:00:00
# (~12-19 h (dt 3-5x job 3068's))
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
# (porous 78,489, free 163,571, 242,060 cells: bath plane at y 0.333 mm, as job 3068)
./Allpre
grep -q "porous 78,489, free 163,571" log.initFields || { echo "ERROR: mesh differs from the laptop build"; exit 1; }
# solver log in ./logs during the run (not the node /tmp), filtered at the end to every 100th step + the
# last 400 lines (../../tools/runTools.sh)
LOG_DIR=logs LOG_EVERY=100 ./run

echo "End: $(date)"
