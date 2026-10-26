#!/bin/bash
# SLURM job of the REV (wicking along y, water-only reservoir, saturated rows) on mini01.
# The job builds the case itself (./Allpre: mesh, eps/K, initial alpha) from the pulled repo, then runs it.
# Needs on mini01: the repo .venv with numpy, scipy, trimesh, rtree (python3 -m venv .venv && .venv/bin/pip install
# numpy scipy trimesh rtree, at the repo root) and the solver of9-port be1a3ab or later (pull, wmake libso in
# libraries/porousInterfaceProperties, wmake in the solver).
# Submit from this folder with sbatch job.slurm after checking the load with squeue; never ./run there.
#SBATCH --job-name=REVwick
#SBATCH --partition=global
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --mem=16G
#SBATCH --time=72:00:00
# (10 ms; laptop 4 cores: 0.5 ms in 1.6 h; cost on mini01 not measured yet: check the log after an hour)
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

N=$(foamDictionary -entry N -value caseSetup)
if [ "$N" -ne "${SLURM_NTASKS}" ]; then
    echo "ERROR: N = $N in caseSetup but --ntasks = ${SLURM_NTASKS}"
    exit 1
fi
if ! ../../.venv/bin/python -c "import numpy, trimesh, rtree" 2>/dev/null; then
    echo "ERROR: no repo .venv with numpy, trimesh and rtree (see the top of this file)."
    exit 1
fi

chmod +x Allpre run clean
# mesh and initial fields from the repo scripts (~20 s); the counts must match the laptop build
# (porous 78,528, free 163,532, 242,060 cells)
./Allpre
grep -q "porous 78,528, free 163,532" log.initFields || { echo "ERROR: mesh differs from the laptop build"; exit 1; }
# solver log in ./logs during the run (not the node /tmp), filtered at the end to every 100th step + the
# last 400 lines (../tools/runTools.sh)
LOG_DIR=logs LOG_EVERY=100 ./run

echo "End: $(date)"
