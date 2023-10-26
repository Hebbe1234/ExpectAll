import argparse
import time
import topology
from bdd import RWAProblem, pretty_print, BDD
from demands import Demand
import networkx as nx 
from itertools import permutations
from demands import Demand
from topology import get_demands
from topology import get_nx_graph
from networkx import digraph
from networkx import MultiDiGraph


if __name__ == "__main__":
	
    parser = argparse.ArgumentParser("mainbdd.py")
    parser.add_argument("--filename", type=str, help="file to run on")
    parser.add_argument("--wavelengths", default=10, type=int, help="number of wavelengths")
    parser.add_argument("--demands", default=10, type=int, help="number of deamdns")
    args = parser.parse_args()

    G = get_nx_graph("./topologies/topzoo/"+args.filename)
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    demands = get_demands(G, args.demands)
    types = [BDD.ET.LAMBDA, BDD.ET.DEMAND, BDD.ET.PATH, BDD.ET.EDGE, BDD.ET.SOURCE, BDD.ET.TARGET, BDD.ET.NODE]

    start_time_all = time.perf_counter()

    forced_order = [BDD.ET.LAMBDA, BDD.ET.EDGE, BDD.ET.NODE]
    ordering = [t for t in types if t not in forced_order]
    p = permutations(ordering)

    start_time_rwa = time.perf_counter()
    rwa = RWAProblem(G, demands, forced_order+[*ordering], args.wavelengths, other_order =True, generics_first=False)

    end_time_all = time.perf_counter()  

    solve_time = end_time_all - start_time_rwa
    all_time = end_time_all - start_time_all

    print("solve time, all time")
    print(solve_time,",", all_time)