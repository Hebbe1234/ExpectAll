#!/bin/bash

SRC=$1
FILENAME=$2
OUT=$3
RUNFILE=$4
EXPERIMENT=$5
WAVELENGHTHS=$6
NUMBERDEMANDS=$7
STARTDEMAND=$8
INCREMENT=$9

demands=()

for ((d=0; d<$NUMBERDEMANDS; d++));
do
	demands+=($(($STARTDEMAND+$d*$INCREMENT)))
done


directory_name="res_$FILENAME"
mkdir $OUT/$directory_name

for dem in "${demands[@]}";
do
        output_file="$OUT/$directory_name/output${dem}.txt"

        sbatch ./run_single.sh $SRC $FILENAME $output_file $WAVELENGHTHS $dem $RUNFILE $EXPERIMENT 
done

exit
