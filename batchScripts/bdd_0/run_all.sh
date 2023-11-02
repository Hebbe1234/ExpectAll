#!/bin/bash

DIR=$1
DEMANDS=$2

GML_NAME=""






cd ../../

mkdir out
mkdir out/bdd_0


cd batchScripts/bdd_0



#for file in "$DIR"/*
cat $DIR | while read filename; do bash ./run_demands.sh ${filename} 5 10 15 20; done 
#do

#    GML_NAME=$(basename $file)    

 #   bash ./run_demands.sh $GML_NAME 5 10 15 20
#done

# Additional commands or post-processing can go here
exit
