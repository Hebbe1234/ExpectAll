#!/bin/bash

SRC=$1
TOPOLOGYPATH=$2
DIR=$3
OUT=$4
RUNFILE=$5
EXPERIMENT=$6
WAVELENGTHS=$7
NUMBERDEMANDS=$8
STARTDEMAND=$9
INCREMENT=${10}
BASHFILE=${11}

echo "" > fredstesting.txt

mkdir $OUT

jobs=""

while read filename || [ -n "$filename" ]; do jobs+="$(bash $BASHFILE $SRC $TOPOLOGYPATH ${filename} $OUT $RUNFILE $EXPERIMENT $WAVELENGTHS $NUMBERDEMANDS $STARTDEMAND $INCREMENT),"; done < $DIR 

echo $jobs >> fredstesting.txt
jobs=${jobs%?}

echo 
echo "start run_all" >> fredstesting.txt
echo $jobs >> fredstesting.txt
echo "end run_all" >> fredstesting.txt

exit
