#!/bin/bash

SRC=$1
FILENAME=$2
OUT=$3
RUNFILE=$4
EXPERIMENT=$5
DEMANDS=$6
NUMBERWAVELENGTHS=$7
STARTWAVELENGTH=$8
INCREMENT=$9

wavelengths=()

for ((d=0; d<$NUMBERWAVELENGTHS; d++));
do
	wavelengths+=($(($STARTWAVELENGTH+$d*$INCREMENT)))
done


directory_name="wave_res_$FILENAME"
mkdir $OUT/$directory_name

for wav in "${wavelengths[@]}";
do
        output_file="$OUT/$directory_name/output${wav}.txt"

        sbatch ./run_single.sh $SRC $FILENAME $output_file $wav $DEMANDS $RUNFILE $EXPERIMENT 
done

exit
