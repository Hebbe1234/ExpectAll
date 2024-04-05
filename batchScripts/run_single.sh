#!/bin/bash
#SBATCH --time=18:00:00
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
python3 -u "${args[@]}" --result_output="$outdir/results/$job_id.json" --bdd_output="$outdir/results/$job_id.json" --replication_output_file_prefix="$outdir/results/$job_id"  > $outdir/logs/$job_id.txt

# Deactivate the virtual environment
deactivate



# Additional commands or post-processing can go here
exit
