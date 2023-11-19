#!/bin/bash
#SBATCH --time=48:00:00
#SBATCH --mail-user=rhebsg19@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --partition=dhabi
#SBATCH --mem=10G


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
output_file="../out/$OUTPUT/${PREFIX}_${FILENAME}.txt"
# Run your Python script
echo $TASK_ID > $output_file

python3 -u reordering.py --filename=$FILENAME --other_order=$OTHER_ORDER --generics_first=$GENERICS_FIRST --split=$SPLIT --num_splits=$NUM_SPLITS--timeout=$TIMEOUT >> $output_file
 
# Deactivate the virtual environment
deactivate
# Additional commands or post-processing can go here
exit
