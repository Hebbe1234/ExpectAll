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

<<<<<<< HEAD
cat $DIR | while read filename || [ -n "$filename" ]; do bash ./run_demands.sh ${filename} $OUT $RUNFILE $EXPERIMENT "$OUT $COMPAREWITH"; done 
=======
cat $DIR | while read filename || [ -n "$filename" ]; do bash ./run_wavelengths.sh ${filename} $OUT $RUNFILE $EXPERIMENT "$OUT $COMPAREWITH"; done 
>>>>>>> main

# Additional commands or post-processing can go here
exit
