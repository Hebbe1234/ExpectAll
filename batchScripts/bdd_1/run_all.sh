#!/bin/bash

DIR=$1
DEMANDS=$2

GML_NAME=""






cd ../../

mkdir out
mkdir out/bdd_1


cd batchScripts/bdd_1



#for file in "$DIR"/*
#do

#    GML_NAME=$(basename $file)

cat $DIR | while read filename; do bash ./run_demands.sh $filename 5 10 15 16; done


# Additional commands or post-processing can go here
exit
