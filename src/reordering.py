import argparse
import math
import time

import sys

class DevNull:
    def write(self, msg):
        pass


from networkx import MultiDiGraph
from bdd import RWAProblem, BDD
from bdd_edge_encoding import RWAProblem as RWAProblem_edge_encoding, BDD as BDD_edge_encoding
from demands import Demand
from topology import get_demands
from topology import get_nx_graph
from dd.autoref import BDD as _BDD
import re
from itertools import permutations, chain, combinations,combinations_with_replacement
from call_function_with_timeout import SetTimeout

def build_rwa(G: MultiDiGraph, demands: dict[int, Demand], ordering: list[BDD.ET], wavelengths: int, group_by_edge_order = False, generics_first = False, with_sequence = False, wavelength_constrained=False, binary=True):
    rwa = RWAProblem(G, demands, ordering, wavelengths, group_by_edge_order=group_by_edge_order, generics_first=generics_first, with_sequence=False)
    t2 = time.perf_counter()
    return (len(rwa.base.bdd), t2)

def build_rwa_edge_encoding(G: MultiDiGraph, demands: dict[int, Demand], ordering: list[BDD_edge_encoding.ET], wavelengths: int, group_by_edge_order = False, generics_first = False, with_sequence = False, wavelength_constrained=False, binary=True):
    rwa = RWAProblem_edge_encoding(G, demands, ordering, wavelengths, group_by_edge_order=group_by_edge_order, generics_first=generics_first, with_sequence=False)
    t2 = time.perf_counter()
    print(rwa.rwa.count())
    return  (len(rwa.base.bdd), t2)

def list_to_dict(c):
    return {var: level for level, var in enumerate(c)}

def powerset(iterable):
    s = list(iterable)  # allows duplicate elements
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

def type_tuple_to_string(tuple, prefixes):
    return "".join([prefixes[t] for t in list(tuple)])


if __name__ == "__main__":

    parser = argparse.ArgumentParser("mainreordering.py")
    parser.add_argument("--filename", type=str, help="file to run on")
    parser.add_argument("--experiment", default="aseline", type=str, help="thing to run on")
    parser.add_argument("--wavelengths", default=5, type=int, help="number of wavelengths")
    parser.add_argument("--demands", default=5, type=int, help="number of demands")
    parser.add_argument("--group_by_edge_order", default="False", type=str, help="other order")
    parser.add_argument("--generics_first", default="False", type=str, help="generics first")
    parser.add_argument("--split", default=1, type=int, help="what split to run?")
    parser.add_argument("--num_splits", default=1, type=int, help="how many splits?")
    parser.add_argument("--index", default="0", type=int, help="Split index")
    parser.add_argument("--timeout", default="60", type=int, help="Timeout in seconds")
    args = parser.parse_args()

    #sys.stderr = DevNull()


    group_by_edge_order = args.group_by_edge_order == "true"
    generics_first = args.generics_first == "true"

    G = get_nx_graph("./topologies/topzoo/"+args.filename)
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    demands = get_demands(G, args.demands)

    types = []
    if args.experiment == "baseline": 
        types = [BDD.ET.LAMBDA, BDD.ET.DEMAND,  BDD.ET.EDGE, BDD.ET.SOURCE, BDD.ET.TARGET, BDD.ET.NODE, BDD.ET.PATH]
    elif args.experiment == "edge_encoded":
        types = [BDD_edge_encoding.ET.DEMAND,  BDD_edge_encoding.ET.EDGE, BDD_edge_encoding.ET.SOURCE, BDD_edge_encoding.ET.TARGET, BDD_edge_encoding.ET.NODE, BDD_edge_encoding.ET.PATH]

    min_t_p = None
    min_m_p = None
    min_len = math.inf


    split_size = math.ceil(math.factorial(len(types)) / args.num_splits)
    indexes_to_run = [i for i in range((args.split - 1) * split_size, (args.split) * split_size)]
    for i, t_p in enumerate(permutations(types)):
        if args.index >= len(indexes_to_run):
            continue
        
        if i != indexes_to_run[args.index]:
            continue
            
        build_func = None
        prefixes = BDD.prefixes
        print(f"Running on perm {i} - done after {indexes_to_run[-1]}")
        if args.experiment == "baseline": 
            build_func = build_rwa
        elif args.experiment == "edge_encoded":
            prefixes = BDD_edge_encoding.prefixes
            build_func = build_rwa_edge_encoding

        if build_func is None:
            exit(1)
        
        t1 = time.perf_counter()
        print(f"Building RWA Problem for (group_by_edge_order = {group_by_edge_order} & generics_first = {generics_first} & order = {type_tuple_to_string(t_p, prefixes)}): ")
        
        (bdd_len, t2) = build_func(G, demands, list(t_p), args.wavelengths, group_by_edge_order =group_by_edge_order, generics_first=generics_first, with_sequence=False)
        
        # if error_message:
        #     print(error_message)
        
        # if is_timeout:
        #     print(f"{args.filename}; {i}; {group_by_edge_order}; {generics_first}; {type_tuple_to_string(t_p, prefixes)}; timeout; timeout")
        #     continue
        
    

        print(f"{args.filename}; {i}; {group_by_edge_order}; {generics_first}; {type_tuple_to_string(t_p, prefixes)}; {bdd_len}; {t2-t1}")
        print(f"")

        if bdd_len < min_len:
            min_t_p = t_p
            min_len = bdd_len

    print(min_len)
    print(min_t_p)

