#!/bin/bash
#SBATCH --time=0:05:00
#SBATCH --mail-user=mpha19@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --partition=naples
#SBATCH --mem=8gb



# Run your Python script
python3 ../src/simpleOutput.py  > test.txt

exit