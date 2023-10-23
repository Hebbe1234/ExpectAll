import topology
from bdd import RWAProblem, pretty_print, BDD
from demands import Demand
import networkx as nx 
from itertools import permutations

if __name__ == "__main__":
    G = topology.get_nx_graph(topology.TOPZOO_PATH +  "/AI3.gml")
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/four_node.dot"))

    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
        
    demands = topology.get_demands(G, 2)
    demands = {0: Demand("A", "B"), 
               1: Demand("B", "D"), 
               2: Demand("C", "B"), 
               3: Demand("A", "B"),
               4: Demand("A", "D"),
                5: Demand("B", "A"),
                6: Demand("C", "B"),
                7: Demand("D", "B"),
                8: Demand("A", "C"),
            #    9: Demand("B", "A")
               }
    print(demands)
    
    ordering = [BDD.ET.DEMAND, BDD.ET.PATH, BDD.ET.EDGE, BDD.ET.SOURCE, BDD.ET.TARGET, BDD.ET.NODE]
    p = permutations(ordering)
    
    for i,o in enumerate(p):
        print(f"ordering being checked: {o}")
        # rwa = RWAProblem(G, demands, [*o], 5, other_order =False, generics_first=False)
        # rwa = RWAProblem(G, demands, [*o], 5, other_order =False, generics_first=True)
        rwa = RWAProblem(G, demands, [BDD.ET.LAMBDA]+[*o], 5, other_order =True, generics_first=False)
        rwa = RWAProblem(G, demands, [BDD.ET.LAMBDA]+[*o], 5, other_order =True, generics_first=True)
        print(rwa.rwa.expr.count())
    
    #rwa.print_assignments(true_only=True, keep_false_prefix="l")