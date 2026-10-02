#!/bin/bash
# SLURM job for this case on mini01 (see the mini01 SLURM guide).
# Submit from this folder with sbatch job.slurm after checking the load with
# squeue (../slurmSubmit.sh queues it behind every active job instead, as the
# guide asks), never with ./run, bash job.slurm or ./job.slurm.
#SBATCH --job-name=yarnImpes
#SBATCH --partition=global
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --mem=10G
#SBATCH --time=24:00:00
# (~10 h estimated on 4 free cores)
#SBATCH --output=Log_%x_%j.log
#SBATCH --error=Err_%x_%j.err
#SBATCH --mail-user=martin.sinegre@gmail.com
#SBATCH --mail-type=END,FAIL

# OpenFOAM 9 environment (sourced before set -e: the bashrc may return non-zero)
source /opt/OpenFOAM-9/etc/bashrc

set -e
cd "${SLURM_SUBMIT_DIR}"

echo "Job ID: ${SLURM_JOB_ID}"
echo "Host: $(hostname)"
echo "Directory: $(pwd)"
echo "Allocated tasks: ${SLURM_NTASKS}"
echo "Solver: $(which impesFoam)"
echo "Start time: $(date)"

# The run script decomposes and starts mpirun with N from caseSetup: it must
# match the number of tasks requested above
N=$(foamDictionary -entry N -value caseSetup)
if [ "$N" -ne "${SLURM_NTASKS}" ]; then
    echo "ERROR: N = $N in caseSetup but --ntasks = ${SLURM_NTASKS}"
    exit 1
fi

chmod +x run clean
# Solver log in ./logs during the run (not the node /tmp), filtered at the end
# to every 100th time step + the last 400 lines (../runTools.sh)
LOG_DIR=logs LOG_EVERY=100 ./run

echo "End time: $(date)"
echo "Job completed successfully."
