import topology
from bdd import RWAProblem, pretty_print
from demands import Demand
import networkx as nx 
if __name__ == "__main__":
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/four_node.dot"))
    G = topology.get_nx_graph(topology.TOPZOO_PATH +  "/AI3.gml")

    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
        
    demands = topology.get_demands(G, 2)
    print(demands)
    rwa = RWAProblem(G, demands, 1)
    print(rwa.rwa.expr.count())
    # rwa.print_assignments()