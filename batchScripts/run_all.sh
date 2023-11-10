#!/bin/bash

SRC=$1
DIR=$2
OUT=$3
RUNFILE=$4
EXPERIMENT=$5
WAVELENGTHS=$6
NUMBERDEMANDS=$7
STARTDEMAND=$8
INCREMENT=$9
BASHFILE=${10}


mkdir $OUT

cat $DIR | while read filename || [ -n "$filename" ]; do bash $BASHFILE $SRC ${filename} $OUT $RUNFILE $EXPERIMENT $WAVELENGTHS $NUMBERDEMANDS $STARTDEMAND $INCREMENT; done 

# Additional commands or post-processing can go here
exit
