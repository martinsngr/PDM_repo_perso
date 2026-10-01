#!/bin/bash
# Submits ./job.slurm on mini01 behind every job currently running, pending or
# completing (mini01 SLURM guide, section 5: the partition allows
# oversubscription, so a plain sbatch could start next to those jobs).
# Usage, from a case folder:  ../slurmSubmit.sh
# Then check that the job is PD with reason "Dependency" while the earlier
# jobs are active:  squeue -u $USER

if [ ! -f job.slurm ]; then
    echo "ERROR: no job.slurm in $PWD (run this from the case folder)"
    exit 1
fi

ACTIVE_JOBS=$(squeue -h -t RUNNING,PENDING,COMPLETING -o "%A" | sort -u | paste -sd: -)
if [ -n "$ACTIVE_JOBS" ]; then
    echo "The new simulation will wait for jobs: $ACTIVE_JOBS"
    sbatch --dependency=afterany:$ACTIVE_JOBS job.slurm
else
    echo "The queue is empty. Submitting the simulation normally."
    sbatch job.slurm
fi
