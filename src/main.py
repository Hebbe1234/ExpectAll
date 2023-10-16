import topology
from bdd import RWAProblem, pretty_print
from demands import Demand
import networkx as nx 
if __name__ == "__main__":
    G = topology.get_nx_graph(topology.TOPZOO_PATH +  "/AI3.gml")
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/simple_net.dot"))

    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
        
    demands = topology.get_demands(G, 3)
    demands = {0: Demand("A", "B"), 1: Demand("A", "B"), 2: Demand("A", "B")}
    print(demands)
    rwa = RWAProblem(G, demands, 2)
    print(rwa.rwa.expr.count())
    
    rwa.print_assignments(true_only=True, keep_false_prefix="l")