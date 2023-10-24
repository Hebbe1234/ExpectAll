#!/bin/bash

DIR=$1
WAVELENGTHS=$2
DEMANDS=$3


GML_NAME=""

cd ../

mkdir out
mkdir out/mip

cd src 

python3.9 -m venv venv #TODO change to actual version we want to use
source venv/bin/activate
pip install pulp networkx matplotlib pydot
deactivate

cd ../batchScripts

num_demands=(1) #array of number of demands to run

for file in "$DIR"/*
do

    GML_NAME=$(basename $file)    

    bash ./run_single_mip_for_many_demand.sh $GML_NAME $num_demands
done

# Additional commands or post-processing can go here
exit