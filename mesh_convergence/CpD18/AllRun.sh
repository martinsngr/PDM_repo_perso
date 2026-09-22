#!/bin/sh

#Main script for running simulations
#Check that you have modified the caseSetup file before starting Allrun

# Source tutorial run functions
. $WM_PROJECT_DIR/bin/tools/RunFunctions

# Number of cores
N=4

cp -r 0/ 0.bkp/


./makeMesh


ERROR_CODE=$?
if [ $ERROR_CODE -ne 0 ]; then
    echo "\nError:"
    echo "Mesh creation failed!\n" >&2
    exit $ERROR_CODE
fi


if [ $N -eq 1 ]; then

    simpleFoam -noFunctionObjects > log1.simpleFoam
else
    ./decompose

    ERROR_CODE=$?
    if [ $ERROR_CODE -ne 0 ]; then
        exit $ERROR_CODE
    fi

    echo "Running $(getApplication) in parallel on $PWD using $N cores"
    mpirun -np $N simpleFoam -parallel -noFunctionObjects > log1.simpleFoam

    if [ $? -eq 0 ]; then
        reconstructPar -latestTime

        ERROR_CODE=$?
        if [ $ERROR_CODE -ne 0 ]; then
            exit $ERROR_CODE
        fi

        # rm -rf processor*
    fi
fi

simpleFoam -postProcess -latestTime > log1.postProcess