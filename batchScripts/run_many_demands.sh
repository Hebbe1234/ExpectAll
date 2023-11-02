#!/bin/bash

DIR=$1
OUT=$2
EXPERIMENT=$3

cd ../

mkdir out
mkdir out/$OUT


cd batchScripts


cat $DIR | while read filename; do bash ./run_demands.sh ${filename} $OUT $EXPERIMENT 5 10 15 20; done 

# Additional commands or post-processing can go here
exit
