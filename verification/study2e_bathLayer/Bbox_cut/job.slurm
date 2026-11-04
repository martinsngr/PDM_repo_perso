#!/bin/bash
# SLURM job of Bbox_cut (study 2e, ../README.md) on mini03: builds the case (./Allpre: mesh, fields, ~1 min with embreex),
# then runs it to 3e-3 s on 4 cores. Needs the repo .venv (numpy, scipy, trimesh==5.1.0, rtree, embreex) and the
# solver of9-port 8a97d02 or later. Submit from this folder: sbatch job.slurm. Not requeued after a node crash (a requeue would rerun Allpre): resubmit by hand.
#SBATCH --job-name=2eBboxC
#SBATCH --partition=global
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --mem=16G
#SBATCH --time=12:00:00
#SBATCH --no-requeue
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
if ! ../../../.venv/bin/python -c "import numpy, trimesh, rtree" 2>/dev/null; then
    echo "ERROR: no repo .venv with numpy, trimesh and rtree."
    exit 1
fi
chmod +x Allpre run clean ../buildCase.sh
./Allpre
LOG_DIR=logs LOG_EVERY=20 ./run
echo "End: $(date)"
