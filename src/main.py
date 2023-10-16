import topology
from bdd import RWAProblem, pretty_print
from demands import Demand

if __name__ == "__main__":
    G = topology.get_nx_graph(topology.TOPZOO_PATH +  "\\AI3.gml")

    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
        
    demands = topology.get_demands(G, 5)
    rwa = RWAProblem(G, demands, 3)
    rwa.print_assignments()