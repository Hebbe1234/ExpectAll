
#!/bin/bash
#SBATCH --time=0:05:00
#SBATCH --mail-user=mpha19@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --partition=naples
#SBATCH --mem=15000

DIR=$1


GML_NAME=""

python3 -m venv venv
source venv/bin/activate
pip install pulp networkx matplotlib pydot
deactivate

for file in "$DIR"/*
do

    GML_NAME=$(basename $file)    
    # path for given 
	echo $GML_NAME
	echo $file
    bash ./run_single_mip_for_many_demand.sh $GML_NAME 1 2 
done

# Additional commands or post-processing can go here
exit