#!/bin/bash

#SBATCH --mail-user=s316765@studenti.polito.it
#SBATCH --mail-type=NONE                   # NONE, BEGIN, END, FAIL, REQUEUE, ALL, TIME_LIMIT, TIME_LIMIT_90
# #SBATCH -e Err.err                       # standard error file
#SBATCH -o Log.log                      # standard output file
#SBATCH --account=mliprandi             # account name
#SBATCH --mem=10G                           # Memory Size (maximum of 128G per node)
#SBATCH -t 24:00:00                        # Wall Clock Limit

######################################

#SBATCH --job-name=dp0              # Name of job
#SBATCH -p global                          # Queue
#SBATCH -N1 -n4                           # <n> cores on <N> nodes

/bin/echo " "
/bin/echo Running on host: $SLURM_SUBMIT_HOST
/bin/echo In directory: $SLURM_SUBMIT_DIR 
/bin/echo "Got ${SLURM_NTASKS} processors."
/bin/echo " "


source /opt/openfoam9/etc/bashrc

python3 bounding.py
chmod +x AllRun.sh
chmod +x AllClean
chmod +x decompose
chmod +x makeMesh
./AllRun.sh 

python3 pythonPostProcess.py

# # If you are using a singularity container, comment previous lines and use the following commands

# SIF_IMAGE=/path/to/container

# singularity run $SIF_IMAGE python3 stmRun.py
# singularity run $SIF_IMAGE ./Allrun
# singularity run $SIF_IMAGE python3 pythonPostProcess.py
