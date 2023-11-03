
#!/bin/bash

FILENAME=$1
OUT=$2
RUNFILE=$3
EXPERIMENT=$4
TOGRAPH=$5




# takes demands as array
wavelengths=( 1 2 3 4 5 6 7 8 9 10 )

cd ../out/$OUT
directory_name="res_$FILENAME"
mkdir "$directory_name"  

cd ../../batchScripts

for w in "${wavelengths[@]}";
do
        output_file="../out/$OUT/$directory_name/output${w}.txt"

        sbatch ./run_single.sh $FILENAME $output_file $w 10 $RUNFILE $EXPERIMENT "${TOGRAPH}" 
done

exit
