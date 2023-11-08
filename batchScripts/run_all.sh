#!/bin/bash

DIR=$1
OUT=$2
RUNFILE=$3
EXPERIMENT=$4
COMPAREWITH=$5

cd ../

mkdir out
mkdir out/$OUT


cd batchScripts

cat $DIR | while read filename || [ -n "$filename" ]; do bash ./run_demands.sh ${filename} $OUT $RUNFILE $EXPERIMENT "$OUT $COMPAREWITH"; done 

# Additional commands or post-processing can go here
exit
