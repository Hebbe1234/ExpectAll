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

def baseline(G, order, demands, wavelengths):
    rw = RWAProblem(G, demands, order, wavelengths, other_order =True, generics_first=False, with_sequence=False)
    return rw.rwa.count() > 0

def increasing(G, order, demands, wavelengths):
    for w in range(1,wavelengths+1):
        #print(f"w: {w}")
        rw1 = RWAProblem(G, demands, order, w, other_order =True, generics_first=False, with_sequence=False)
        if rw1.rwa.count() > 0:
           # print(rw1.get_assignments(1)[0])
            return True
            
    return False

def print_demands(filename, demands, wavelengths):
    print("graph: ", filename, "wavelengths: ", wavelengths, "demands: ")
    print(demands)

def wavelength_constrained(G, order, demands, wavelengths):
    rw = RWAProblem(G, demands, order, wavelengths, other_order =True, generics_first=False, with_sequence=False, wavelength_constrained=True)
    return True

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser("mainbdd.py")
    parser.add_argument("--filename", type=str, help="file to run on")
    parser.add_argument("--wavelengths", default=10, type=int, help="number of wavelengths")
    parser.add_argument("--demands", default=10, type=int, help="number of demands")
    parser.add_argument("--experiment", default="baseline", type=str, help="experiment to run")
    args = parser.parse_args()

    G = get_nx_graph("./topologies/topzoo/"+args.filename)
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    demands = get_demands(G, args.demands)
    types = [BDD.ET.LAMBDA, BDD.ET.DEMAND, BDD.ET.PATH, BDD.ET.EDGE, BDD.ET.SOURCE, BDD.ET.TARGET, BDD.ET.NODE]

    start_time_all = time.perf_counter()

    forced_order = [BDD.ET.LAMBDA, BDD.ET.EDGE, BDD.ET.NODE]
    ordering = [t for t in types if t not in forced_order]

    solved = False
    
    start_time_rwa = time.perf_counter()

    if args.experiment == "baseline":
        solved = baseline(G, forced_order+[*ordering], demands, args.wavelengths)
    elif args.experiment == "increasing":
        solved = increasing(G, forced_order+[*ordering], demands, args.wavelengths)
    elif args.experiment == "wavelength_constraint":
        solved = wavelength_constrained(G, forced_order+[*ordering], demands, args.wavelengths)
    elif args.experiment == "print_demands":
        print_demands(args.filename, demands, args.wavelengths)
        exit(0)

    
    end_time_all = time.perf_counter()  

    solve_time = end_time_all - start_time_rwa
    all_time = end_time_all - start_time_all

    print("solve time, all time, satisfiable")
    print(solve_time,",", all_time, ",", solved)
