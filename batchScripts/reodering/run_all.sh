#!/bin/bash

DIR=$1
OUT=$2
MAX_SPLIT=$3
EXPERIMENT=$4

cd ../../

mkdir out
mkdir out/$OUT


cd batchScripts/reodering

group_by_edge_order=( true false )
interleave_lambda_binary_vars=( true false )
generics_first=( true false )
split=( 1 2 3 4 5 6 7 8 9 10 )

for s in "${split[@]}";
do
    for oo in "${group_by_edge_order[@]}";
    do
        for lb in "${interleave_lambda_binary_vars[@]}";
        do
            for gf in "${generics_first[@]}";
            do
                cat $DIR | while read filename || [ -n "$filename" ]; do sbatch --array=0-$MAX_SPLIT ./run_single.sh ${filename} $OUT $oo $lb $gf "${s}_${oo}_${lb}_${gf}" $s ${split[-1]} 60 $EXPERIMENT; done 
            done
        done
    done
done

# Additional commands or post-processing can go here
exit
