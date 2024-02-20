#!/bin/bash

SRC=$1
TOPOLOGYPATH=$2
FILENAME=$3
OUT=$4
RUNFILE=$5
EXPERIMENT=$6
WAVELENGHTHS=$7
NUMBERDEMANDS=$8
STARTDEMAND=$9
INCREMENT=${10}

demands=()

for ((d=0; d<$NUMBERDEMANDS; d++));
do
	demands+=($(($STARTDEMAND+$d*$INCREMENT)))
done


directory_name="res_$FILENAME"
mkdir $OUT/$directory_name


jobArray=()

for dem in "${demands[@]}";
do
        output_file="$OUT/$directory_name/output${dem}.txt"

        id=$(sbatch ./run_single.sh $SRC $TOPOLOGYPATH $FILENAME $output_file $WAVELENGHTHS $dem $RUNFILE $EXPERIMENT)
		jobArray+=($id) 
done

jobs="$(IFS=:; echo "${jobArray[*]}")"

echo $jobs
echo $FILENAME >> fromdemands.txt
echo $jobs >> fromdemands.txt


exit
