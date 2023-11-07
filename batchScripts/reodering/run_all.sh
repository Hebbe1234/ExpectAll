#!/bin/bash

DIR=$1
OUT=$2

cd ../../

mkdir out
mkdir out/$OUT


cd batchScripts/reodering

cat $DIR | while read filename || [ -n "$filename" ]; do sbatch ./run_single.sh ${filename} $OUT; done 

# Additional commands or post-processing can go here
exit
