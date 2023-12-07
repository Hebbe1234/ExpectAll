#!/bin/bash

DIR=$1
OUT=$2

cd ../../

mkdir out
mkdir out/$OUT


cd batchScripts/reodering

group_by_edge_order=( true false )
generics_first=( true false )
split=( 1 2 3 4 5 6 7 8 9 10 )

for s in "${split[@]}";
do
    for oo in "${group_by_edge_order[@]}";
    do
        for gf in "${generics_first[@]}";
        do
            cat $DIR | while read filename || [ -n "$filename" ]; do sbatch --array=0-503 ./run_single.sh ${filename} $OUT $oo $gf "${s}_${oo}_${gf}" $s ${split[-1]} 60; done 
        done
    done
done

# Additional commands or post-processing can go here
exit
