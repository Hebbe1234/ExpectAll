#!/bin/bash

DIR=$1
DEMANDS=$2

GML_NAME=""

cd ../../

mkdir out
mkdir out/bdd_1

cd src 

python3 -m venv bdd_venv #TODO change to actual version we want to use
source bdd_venv/bin/activate
python3 -m pip install networkx matplotlib pydot dd networkx
deactivate

cd ../batchScripts/bdd_1


for file in "$DIR"/*
do

    GML_NAME=$(basename $file)    

    bash ./run_demands.sh $GML_NAME $DEMANDS
done

# Additional commands or post-processing can go here
exit
