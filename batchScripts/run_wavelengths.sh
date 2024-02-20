#!/bin/bash

SRC=$1
TOPOLOGYPATH=$2
FILENAME=$3
OUT=$4
RUNFILE=$5
EXPERIMENT=$6
DEMANDS=$7
NUMBERWAVELENGTHS=$8
STARTWAVELENGTH=$9
INCREMENT=${10}

wavelengths=()

for ((d=0; d<$NUMBERWAVELENGTHS; d++));
do
	wavelengths+=($(($STARTWAVELENGTH+$d*$INCREMENT)))
done


directory_name="res_$FILENAME"
mkdir $OUT/$directory_name
jobArray=()



for wav in "${wavelengths[@]}";
do
        output_file="$OUT/$directory_name/output${wav}.txt"
        id=$(sbatch ./run_single.sh $SRC $TOPOLOGYPATH $FILENAME $output_file $wav $DEMANDS $RUNFILE $EXPERIMENT)
		jobArray+=$id 
done

jobs="$(IFS=,; echo "${jobArray[*]}")"

echo $jobs


exit
