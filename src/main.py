import topology
from bdd import RWAProblem, pretty_print
from demands import Demand
import networkx as nx 
if __name__ == "__main__":
    G = topology.get_nx_graph(topology.TOPZOO_PATH +  "/AI3.gml")
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/four_node.dot"))

    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
        
    demands = {0: Demand("A", "B"), 
    1: Demand("B", "D"), 
    2: Demand("C", "B"), 
    3: Demand("A", "B"),
    4: Demand("A", "D"),
    5: Demand("B", "A"),
    6: Demand("C", "B"),
    7: Demand("D", "B"),
    8: Demand("A", "C"),
    9: Demand("B", "A")}
    print(demands)
    rwa = RWAProblem(G, demands, 5)
    print(rwa.rwa.expr.count())
    
    #rwa.print_assignments(true_only=True, keep_false_prefix="l")