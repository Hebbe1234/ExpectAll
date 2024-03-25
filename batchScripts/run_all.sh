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
p1=${12}
p2=${13}
p3=${14}
p4=${15}
p5=${16}

mkdir $OUT

jobs=""

echo "" > fromdemands.txt #for logging

while read filename || [ -n "$filename" ]; do jobs+="$(bash $BASHFILE $SRC $TOPOLOGYPATH ${filename} $OUT $RUNFILE $EXPERIMENT $WAVELENGTHS $NUMBERDEMANDS $STARTDEMAND $INCREMENT $p1 $p2 $p3 $p4 $p5):"; done < $DIR 

jobs=${jobs%?}

echo $jobs
 
exit
