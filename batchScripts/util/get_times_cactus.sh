#!/bin/bash

DIRS=$1
SAVEDIR=$2
SAVEFILE=$3

## now loop through the above array
mkdir $SAVEDIR


for dir in $DIRS/*res*;
do
	for output in $dir/*;
	do
		demands=$(basename $output)
		demands="${demands/"output"/""}"
		demands="${demands/".txt"/""}"

		datafile=$SAVEDIR/output$demands
		echo "solve_time" > $datafile;
	done
	break
done



for dir in $DIRS/*res*;
do
	first=true
	instance=0
	for output in $dir/*;
	do
		demands=$(basename $output)
		demands="${demands/"output"/""}"
		demands="${demands/".txt"/""}"

		datafile=$SAVEDIR/output$demands
		grep "true" -ri $output | awk -F"output|\.txt|:| " '{print $4}' >>  $datafile
	done
done
