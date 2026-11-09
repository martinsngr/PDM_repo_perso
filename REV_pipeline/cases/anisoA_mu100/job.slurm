#!/bin/bash
# SLURM job of anisoA_mu100 (REV_pipeline, ../../README.md): anisoA with the air viscosity / 100. Cross-check of tensorA
# with stock anisoImpesFoam, the yarns alone
# (78,489 cells), 30 ms. Builds the case (./Allpre, ~20 s) and runs it; if processor0/ exists (requeued after a crash or
# submitted again), continues from the latest time instead (startFrom latestTime) without rebuilding.
# Needs on the cluster: anisoImpesFoam (porousMultiphaseFoam, wmake in solvers/anisoImpesFoam after the libraries) and
# the repo .venv (numpy, trimesh, rtree, embreex). Submit from this folder with sbatch job.slurm; never ./run there.
#SBATCH --job-name=REVanisoMu
#SBATCH --partition=global
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --mem=8G
#SBATCH --time=72:00:00
#SBATCH --open-mode=append
#SBATCH --output=Log_%x_%j.log
#SBATCH --error=Err_%x_%j.err
#SBATCH --mail-user=martin.sinegre@gmail.com
#SBATCH --mail-type=END,FAIL

# OpenFOAM 9 environment (sourced before set -e: the bashrc may return non-zero)
source /opt/OpenFOAM-9/etc/bashrc

set -e
cd "${SLURM_SUBMIT_DIR}"
. "$WM_PROJECT_DIR/bin/tools/RunFunctions"
. ../../tools/runTools.sh

echo "Job ID: ${SLURM_JOB_ID}  Host: $(hostname)  Directory: $(pwd)"
echo "Allocated tasks: ${SLURM_NTASKS}  Solver: $(which anisoImpesFoam)  Start: $(date)"
command -v anisoImpesFoam > /dev/null || { echo "ERROR: no anisoImpesFoam (build it in porousMultiphaseFoam/solvers/anisoImpesFoam)"; exit 1; }

N=$(foamDictionary -entry N -value caseSetup)
if [ "$N" -ne "${SLURM_NTASKS}" ]; then
    echo "ERROR: N = $N in caseSetup but --ntasks = ${SLURM_NTASKS}"
    exit 1
fi

if [ -d processor0 ]; then
    echo "processor0 exists: continuing from the latest time"
    status=0
    LOG_DIR=logs LOG_EVERY=100 runTmpLog log.anisoImpesFoam mpirun -np "$N" anisoImpesFoam -parallel || status=$?
    rm -f log.reconstructPar
    runApplication reconstructPar -newTimes
    [ "$status" -eq 0 ] || { echo "ERROR: anisoImpesFoam failed (see log.anisoImpesFoam)."; exit 1; }
else
    if ! ../../../.venv/bin/python -c "import numpy, trimesh, rtree" 2>/dev/null; then
        echo "ERROR: no repo .venv with numpy, trimesh and rtree."
        exit 1
    fi
    chmod +x Allpre run clean
    ./Allpre
    # the counts of the laptop build (2026-11-09): tensorA's 78,489 yarn cells, 39,115 yarn-surface faces
    grep -q "78,489 cells" log.toAnisoImpes && grep -q "39115 faces" log.toAnisoImpes \
        || { echo "ERROR: mesh differs from the laptop build"; exit 1; }
    LOG_DIR=logs LOG_EVERY=100 ./run
fi
echo "End: $(date)"
