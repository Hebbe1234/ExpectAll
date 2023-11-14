import argparse
import math
import time
from bdd import RWAProblem, BDD
from topology import get_demands
from topology import get_nx_graph
from dd.autoref import BDD as _BDD
import re
from itertools import permutations, chain, combinations,combinations_with_replacement
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

    args = parser.parse_args()

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

    for i, t_p in enumerate(permutations(types)):
        t1 = time.perf_counter()
        print(f"Building RWA Problem for (other_order = {other_order} & generics_first = {generics_first} & order = {type_tuple_to_string(t_p)}): ")
        rwa = RWAProblem(G, demands, list(t_p), args.wavelengths, other_order =other_order, generics_first=generics_first, with_sequence=False)
        bdd = rwa.base.bdd
        t2 = time.perf_counter()

        print(f"{args.filename}; {i}; {other_order}; {generics_first}; {type_tuple_to_string(t_p)}; {len(bdd)}; {t2-t1}")
        print(f"")

        if len(bdd) < min_len:
            min_t_p = t_p
            min_len = len(bdd)

        del rwa

    print(min_len)
    print(min_t_p)

