import topology
from bdd_edge_encoding import RWAProblem, pretty_print, BDD
from demands import Demand
import networkx as nx 
from itertools import permutations

if __name__ == "__main__":
    G = topology.get_nx_graph(topology.TOPZOO_PATH +  "/AI3.gml")
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/simple_net.dot"))
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/simple_simple_net.dot"))
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/four_node.dot"))

    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
        
    # demands = {1: Demand("C", "D"), 
    #         #    2: Demand("D", "A")
               
    #            }
    demands = topology.get_demands(G, 13, 1)
    print("demands", demands)
    
    types = [BDD.ET.EDGE, BDD.ET.LAMBDA, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH,BDD.ET.SOURCE]
    types = [BDD.ET.EDGE, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH,BDD.ET.SOURCE]
    # forced_order = [BDD.ET.LAMBDA, BDD.ET.EDGE, BDD.ET.NODE]
    # ordering = [t for t in types if t not in forced_order]
    # p = permutations(ordering)

    # Increasing wavelengths
    # for w in range(1,5+1):
    #     print(f"w: {w}")
    #     rw1 = RWAProblem(G, demands, forced_order+[*ordering], w, other_order =True, generics_first=False)
    #     if rw1.rwa.count() > 0:
    #         print(rw1.get_assignments(1)[0])
    #         break    
    
    rw1 = RWAProblem(G, demands, types, wavelengths=4, other_order =True, generics_first=False, binary=True)
    print(len(rw1.base.bdd))
    exit(0)    
    
    # for i,o in enumerate(p):
    #     print(f"ordering being checked: {o}")
    #     # rwa = RWAProblem(G, demands, [*o], 5, other_order =False, generics_first=False)
    #     # rwa = RWAProblem(G, demands, [*o], 5, other_order =False, generics_first=True)
    #     rwa = RWAProblem(G, demands, forced_order+[*o], 5, other_order =True, generics_first=False)
    #     rwa = RWAProblem(G, demands, forced_order+[*o], 5, other_order =True, generics_first=True)
    #     # print(rwa.rwa.count())
    
    #rwa.print_assignments(true_only=True, keep_false_prefix="l")