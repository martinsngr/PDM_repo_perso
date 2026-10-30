#!/bin/bash
# SLURM job restarting the REV_lowpc run from its last complete write (after a crash or a walltime stop).
# Unlike job.slurm it does not run ./Allpre, ./clean or decomposePar: it keeps processor*/, the csv files and
# the logs, and continues from the latest time in processor0 (startFrom latestTime in system/controlDict).
# A last write left incomplete by the crash (files missing or cut short in any processor) is moved to
# processor*/<time>.incomplete and the run starts from the write before it.
# Needs the same N (caseSetup) as the run being continued: the decomposition is reused.
# Submit from this folder with sbatch job_restart.slurm, after scancel of the old job if it is still listed.
#SBATCH --job-name=REVlowpc
#SBATCH --partition=global
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --mem=16G
#SBATCH --time=72:00:00
#SBATCH --output=Log_%x_%j.log
#SBATCH --error=Err_%x_%j.err
#SBATCH --mail-user=martin.sinegre@gmail.com
#SBATCH --mail-type=END,FAIL

# OpenFOAM 9 environment (sourced before set -e: the bashrc may return non-zero)
source /opt/OpenFOAM-9/etc/bashrc

set -e
cd "${SLURM_SUBMIT_DIR}"
. "$WM_PROJECT_DIR/bin/tools/RunFunctions"
. ../tools/runTools.sh

echo "Job ID: ${SLURM_JOB_ID}  Host: $(hostname)  Directory: $(pwd)"
echo "Allocated tasks: ${SLURM_NTASKS}  Solver: $(which hybridPorousInterFoam)  Start: $(date)"

N=$(foamDictionary -entry N -value caseSetup)
if [ "$N" -ne "${SLURM_NTASKS}" ]; then
    echo "ERROR: N = $N in caseSetup but --ntasks = ${SLURM_NTASKS}"
    exit 1
fi
nProc=$(ls -d processor* 2>/dev/null | wc -l)
if [ "$nProc" -ne "$N" ]; then
    echo "ERROR: $nProc processor folders, N = $N: nothing to restart from (or another decomposition)."
    exit 1
fi

# time folders of processor0, latest first (names made only of digits, '.', 'e', '+', '-')
times() { ls processor0 | grep -E '^[0-9.e+-]+$' | sort -g -r; }

# a write is complete if every processor has it with the same number of files as processor0
# and every file ends with the OpenFOAM footer line and holds no NUL byte (a node crash can leave
# zero-filled blocks in files written just before it: the log of job 3055 had some, 2026-10-28)
complete()
{
    _n=$(find "processor0/$1" -type f | wc -l)
    for p in processor*; do
        [ -d "$p/$1" ] || return 1
        [ "$(find "$p/$1" -type f | wc -l)" -eq "$_n" ] || return 1
        for f in $(find "$p/$1" -type f); do
            tail -c 200 "$f" | grep -q '\*\*\*\*\*\* //' || return 1
            [ "$(tr -d '\000' < "$f" | wc -c)" -eq "$(wc -c < "$f")" ] || return 1
        done
    done
}

latest=""
for t in $(times); do
    [ "$t" = 0 ] && break
    if complete "$t"; then
        latest=$t
        break
    fi
    echo "Write $t incomplete: moved to processor*/$t.incomplete"
    for p in processor*; do
        [ -d "$p/$t" ] && mv "$p/$t" "$p/$t.incomplete"
    done
done
[ -n "$latest" ] || { echo "ERROR: no complete write after 0 in processor*/."; exit 1; }
echo "Restarting from t = $latest"

# coded function objects compiled in serial first (inside mpirun the compilation aborts: MPI_ERR_TRUNCATE);
# the csv files are kept as they are (that pass may add t = 0 rows)
for f in liquidBalance.csv waterBudget.csv; do [ -f "$f" ] && cp "$f" "$f.bak"; done
rm -f log.hybridPorousInterFoam.precompile
runApplication -s precompile hybridPorousInterFoam -postProcess -time 0
for f in liquidBalance.csv waterBudget.csv; do [ -f "$f.bak" ] && mv "$f.bak" "$f"; done

# solver log in a new ./logs/REV.XXXXXX/ (the log of the crashed run stays in its own folder there)
echo "Running hybridPorousInterFoam on $PWD using $N cores"
status=0
LOG_DIR=logs LOG_EVERY=100 runTmpLog log.hybridPorousInterFoam mpirun -np "$N" hybridPorousInterFoam -parallel \
    || status=$?
rm -f log.reconstructPar
runApplication reconstructPar -newTimes
if [ "$status" -ne 0 ]; then
    echo "ERROR: hybridPorousInterFoam failed (see log.hybridPorousInterFoam)."
    exit 1
fi

echo "End: $(date)"
