import argparse
import math
import time

import sys

class DevNull:
    def write(self, msg):
        pass


from networkx import MultiDiGraph
from bdd import RWAProblem, BDD
from demands import Demand
from topology import get_demands
from topology import get_nx_graph
from dd.autoref import BDD as _BDD
import re
from itertools import permutations, chain, combinations,combinations_with_replacement
from call_function_with_timeout import SetTimeout

def build_rwa(G: MultiDiGraph, demands: dict[int, Demand], ordering: list[BDD.ET], wavelengths: int, other_order = False, generics_first = False, with_sequence = False, wavelength_constrained=False, binary=True):
    rwa = RWAProblem(G, demands, ordering, wavelengths, other_order=other_order, generics_first=generics_first, with_sequence=False)
    return len(rwa.base.bdd)

def list_to_dict(c):
    return {var: level for level, var in enumerate(c)}

def powerset(iterable):
    s = list(iterable)  # allows duplicate elements
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

def type_tuple_to_string(tuple):
    return "".join([BDD.prefixes[t] for t in list(tuple)])


if __name__ == "__main__":

    parser = argparse.ArgumentParser("mainreordering.py")
    parser.add_argument("--filename", type=str, help="file to run on")
    parser.add_argument("--wavelengths", default=5, type=int, help="number of wavelengths")
    parser.add_argument("--demands", default=5, type=int, help="number of demands")
    parser.add_argument("--other_order", default="False", type=str, help="other order")
    parser.add_argument("--generics_first", default="False", type=str, help="generics first")
    parser.add_argument("--split", default=1, type=int, help="what split to run?")
    parser.add_argument("--num_splits", default=1, type=int, help="how many splits?")
    parser.add_argument("--timeout", default="60", type=int, help="Timeout in seconds")
    args = parser.parse_args()

    # sys.stderr = DevNull()


    other_order = args.other_order == "true"
    generics_first = args.generics_first == "true"

    G = get_nx_graph("./topologies/topzoo/"+args.filename)
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    demands = get_demands(G, args.demands)

    types = [BDD.ET.LAMBDA, BDD.ET.DEMAND,  BDD.ET.EDGE, BDD.ET.SOURCE, BDD.ET.TARGET, BDD.ET.NODE, BDD.ET.PATH]


    min_t_p = None
    min_m_p = None
    min_len = math.inf


    split_size = math.ceil(math.factorial(len(types)) / args.num_splits)
    indexes_to_run = [i for i in range((args.split - 1) * split_size, (args.split) * split_size)]
    for i, t_p in enumerate(permutations(types)):
        if i not in indexes_to_run:
            continue
    
        build_with_timeout = SetTimeout(build_rwa, timeout=args.timeout)

        t1 = time.perf_counter()
        print(f"Building RWA Problem for (other_order = {other_order} & generics_first = {generics_first} & order = {type_tuple_to_string(t_p)}): ")
        
        is_done, is_timeout, error_message, bdd_len = build_with_timeout(G, demands, list(t_p), args.wavelengths, other_order =other_order, generics_first=generics_first, with_sequence=False)
        
        if is_timeout:
            print(f"{args.filename}; {i}; {other_order}; {generics_first}; {type_tuple_to_string(t_p)}; timeout; timeout")
            continue

    
        t2 = time.perf_counter()

        print(f"{args.filename}; {i}; {other_order}; {generics_first}; {type_tuple_to_string(t_p)}; {bdd_len}; {t2-t1}")
        print(f"")

        if bdd_len < min_len:
            min_t_p = t_p
            min_len = bdd_len

    print(min_len)
    print(min_t_p)

