#!/bin/bash
# SLURM job of BfullP_cut (study 2e, ../README.md) on mini03: builds the case (./Allpre: mesh, fields, ~1 min with embreex),
# then runs it to 0.012 s on 12 cores. Needs the repo .venv (numpy, scipy, trimesh==5.1.0, rtree, embreex) and the
# solver of9-port 8a97d02 or later. Submit from this folder: sbatch job.slurm. Requeued after a node crash: continues from the last complete write (job_restart.slurm).
#SBATCH --job-name=2eBfullPC
#SBATCH --partition=global
#SBATCH --nodes=1
#SBATCH --ntasks=12
#SBATCH --mem=8G
#SBATCH --time=36:00:00
#SBATCH --open-mode=append
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
    echo "ERROR: no repo .venv with numpy, trimesh and rtree."
    exit 1
fi
chmod +x Allpre run clean ../buildCase.sh
./Allpre
LOG_DIR=logs LOG_EVERY=100 ./run
echo "End: $(date)"
