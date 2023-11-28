#!/bin/bash
#SBATCH --time=24:00:00
#SBATCH --mail-user=rhebsg19@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --partition=dhabi
#SBATCH --mem=10G
#SBATCH --output=/nfs/home/student.aau.dk/rhebsg19/slurm-output/reordering/reordering-%A_%a.out  # Redirect the output stream to this file (%A_%a is the job's array-id and index)
#SBATCH --error=/nfs/home/student.aau.dk/rhebsg19/slurm-output/reordering/reordering-%A_%a.err   # Redirect the error stream to this file (%A_%a is the job's array-id and index)


let "m=1024*1024*10"
ulimit -v $m

FILENAME=$1
OUTPUT=$2
OTHER_ORDER=$3
GENERICS_FIRST=$4
PREFIX=$5
SPLIT=$6
NUM_SPLITS=$7
TIMEOUT=$8

cd ../../src



# Create and activate a virtual environment
source bdd_venv/bin/activate
output_file="../out/$OUTPUT/${SLURM_ARRAY_TASK_ID}_${PREFIX}_${FILENAME}.txt"
# Run your Python script
echo $TASK_ID > $output_file

MYCMD="python3 -u reordering.py --filename=$FILENAME --other_order=${OTHER_ORDER} --generics_first=${GENERICS_FIRST} --split=${SPLIT} --num_splits=${NUM_SPLITS} --index ${SLURM_ARRAY_TASK_ID} --timeout=${TIMEOUT} >> ${output_file}"
CMD="timeout ${TIMEOUT} /usr/bin/time -f \"@@@%e,%M@@@\" ${MYCMD} >> ${output_file}"
echo "${FILENAME}; ${OTHER_ORDER}; ${GENERICS_FIRST}; ${SPLIT}; ${SLURM_ARRAY_TASK_ID}"  # Log command to slurm output file.
echo "${CMD}"  # Log command to slurm output file.
eval "${CMD}"  # Run the command

 
# Deactivate the virtual environment
deactivate
# Additional commands or post-processing can go here
exit
