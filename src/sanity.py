import argparse
import time
import topology
from bdd import RWAProblem, BDD, pretty_print, Demand
from topology import get_demands
from topology import get_nx_graph   
try:
    from dd.cudd import BDD as _BDD
    from dd.cudd import Function
    has_cudd = True
except ImportError:
   from dd.autoref import BDD as _BDD
   from dd.autoref import Function 
   print("Using autoref... ")
import networkx as nx



def is_invalid_without_count():
    print(":D")

    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/very_simple.dot"))
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    demands = {
                0: Demand("A", "B"), 
                #1: Demand("A", "B"), 
               }
    types = [BDD.ET.EDGE, BDD.ET.LAMBDA, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH,BDD.ET.SOURCE]
    print(":D")
    rwa = RWAProblem(G, demands, types, 1, other_order =True, generics_first=False, with_sequence=False)
    
    print(rwa.rwa.count())
    print(rwa.rwa == rwa.base.bdd.false)
    pretty_print(rwa.base.bdd, rwa.rwa)

def small_bdd_subset_of_larger_for_demands():
    G = get_nx_graph("./topologies/topzoo/Ai3.gml")
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    demands = get_demands(G, 8)
    types = [BDD.ET.EDGE, BDD.ET.LAMBDA, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH,BDD.ET.SOURCE]

    print({i:demands[i] for i in list(demands.keys())[0:-1]})
    print(demands)

    rw1 = RWAProblem(G, {i:demands[i] for i in list(demands.keys())[0:-1]}, types, 8, other_order =True, generics_first=False, with_sequence=False)
    rw2 = RWAProblem(G, demands, types, 8, other_order =True, generics_first=False, with_sequence=False)

    #print(rw1.rwa.count(), rw2.rwa.count())
    base = BDD(G, demands, types, 8, other_order=True, generics_first=False)
    smaller = rw1.base.bdd.copy(rw1.rwa, base.bdd) 
    larger = rw2.base.bdd.copy(rw2.rwa, base.bdd)
    combined = smaller & larger
    #rw3 = rw1.rwa & rw2.rwa
    print(rw1.rwa.count(), rw2.rwa.count())
    print(smaller.count(), larger.count(), combined.count())
    pretty_print(base.bdd, smaller)

if __name__ == "__main__":
    is_invalid_without_count()