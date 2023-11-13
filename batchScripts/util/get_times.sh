#!/bin/bash
## declare an array variable

DIRS=$1

## now loop through the above array
savedir=$(pwd)/csv-data
mkdir $savedir
for dir in $DIRS/*res*;
do
	first=true
	for graph in $dir/*;
	do
		datafile=$savedir/$(basename $dir)-data.csv
		if $first; then echo "wavelength; CPU time" > $datafile; fi
		grep "true" -ri $graph | awk -F"output|\.txt|:| " '{print $2"; "$4}' >> $datafile
		first=false
	done
done


 



