# AllRight

With the increasing demand for higher bandwidth and quality of service in modern networks, the need for fast, resilient networks is in sight for the future. Here, recent advances in elastic optical networks have enabled fine-grained resource allocation for traffic demands, which introduced the Routing and Spectrum Assignment (RSA) problem. State-of-the-art methods for finding optimal solutions to the RSA problem are too slow for real-time practical applications, such as ensuring failure resilience, and faster methods cannot guarantee optimal resource allocation. Moreover, current methods for ensuring failure resilience in classic networking cannot be directly adapted to optical networks, and current methods for optical networks generally rely on over allocation of the spectrum to ensure rapid recovery. 
To this end, we present ExpectAll, a novel approach based on binary decision diagrams (BDDs) to ensure failure resilience for multi-link failures without resorting to spectrum overallocation. Our method efficiently computes solutions to the RSA problem, facilitating optimal failover solutions for any failure scenario involving up to $k$ links. ExpectAll surpasses state-of-the-art methods in both the speed of finding a single optimal solution during a failure and the preparation time required to compute sufficient solutions to ensure resilience against arbitrary large $k$-link failures. Additionally, since ExpectAll can compute and represent all potential solutions, it is adaptable for network operators to find solutions that meet specific desired properties.

# Data
You can find all data used for the paper in the folder `out/Reproduceability` 

# Usage
1. Create a new python virtual environment
2. Install the required packages from `requirements.txt`

## Run ExpectAll
1. Go to `src`
1. Run `main.py`
    * specify topology to run on, number of demands, what BDD should be built and how it should be evaluated.
    * Example: `python main.py --topology ./topologies/japanese_topologies/dt.gml --demands 3 --gapfree --upper_bound --limited --query 3`

## Draw graphs from paper
1. Go to `src/mkplots`
1. Run one of the commands from `commands.md` to generate the correct plot. This uses the data found in `out/Reproduceability`

