#!/bin/bash
#SBATCH --time=1:00:00
#SBATCH --mail-user=rhebsg19@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --partition=dhabi
#SBATCH --mem=16G
#SBATCH --parsable


let "m=1024*1024*50"
ulimit -v $m


# Create and activate a virtual environment
source ../src/bdd_venv/bin/activate
# Run your Python script
python3 -u "${@}"


# Deactivate the virtual environment
deactivate



# Additional commands or post-processing can go here
exit
