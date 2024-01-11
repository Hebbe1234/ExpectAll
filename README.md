# AllRight

The application of Wavelength Division Multiplexers (WDM) in optical fiber networks is a well-known approach to increase bandwidth. A problem that arises for WDM optical fiber networks is the Routing and Wavelength Assignment problem (RWA), as the demands of the network must each be assigned a wavelength without causing wave interference. State-of-the-art tools that solve the RWA problem find only a single solution which provides less flexibility for the network engineers. We present a novel approach to solving the RWA problem by using Binary Decision Diagrams (BDD) to find all possible solutions to the RWA problem. We implement our approach as the tool AllRight and provide different techniques to increase the efficiency of AllRight. We then evaluate AllRight with and without using the techniques by comparing it to the state-of-the-art method Mixed Integer Programming (MIP) that only finds a single solution. From the results, we find that AllRight is less efficient than MIP, but AllRight also finds all possible solutions to the RWA problem as opposed to finding a single solution.

# Data
You can find all the data used for the paper in the Zip-archive `data.zip` 

# Usage
1. Unzip `data.zip` to the root dir of this repo
2. Create a new python virtual environment
3. Install the required packages from `requirements.txt`

## Run different versions of  RWA
1. Go to `src`
1. Run either `run_bdd.py`, `run_dynamic.py`, `run_edge_encoding.py`
    * specify topology to run on, experiment to run, number of wavelengths and number of demands.

## Draw graphs from paper
1. Go to `src/mkplots`
1. Run one of the commands from `commands.txt`

