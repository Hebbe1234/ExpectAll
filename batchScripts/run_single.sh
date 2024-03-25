#!/bin/bash
#SBATCH --time=1:00:00
#SBATCH --mail-user=rhebsg19@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --partition=dhabi
#SBATCH --mem=16G
#SBATCH --parsable


let "m=1024*1024*50"
ulimit -v $m

SRC=$1
TOPOLOGYPATH=$2
FILENAME=$3
OUTPUT=$4
WAVELENGTHS=$5
DEMANDS=$6
RUNFILE=$7
EXPERIMENT=$8
p1=${9}
p2=${10}
p3=${11}
p4=${12}
p5=${13}

# Create and activate a virtual environment
source $SRC/bdd_venv/bin/activate
echo "${FILENAME};"
# Run your Python script
python3 -u $SRC/$RUNFILE --experiment=$EXPERIMENT --filename=$TOPOLOGYPATH$FILENAME --wavelengths=$WAVELENGTHS --demands=$DEMANDS --par1=$p1 --par2=$p2 --par3=$p3 --par4=$p4 --par5=$p5 > $OUTPUT


# Deactivate the virtual environment
deactivate



# Additional commands or post-processing can go here
exit
