from networkx import MultiDiGraph
from demands import Demand
import networkx as nx
import topology
from bdd import BDD, RWAProblem
import matplotlib.pyplot as plt
import pydot

def draw_assignment(assignment: dict[str, bool], base: BDD, topology:MultiDiGraph):
    def power(l_var: str):
        val = int(l_var.replace(base.prefixes[BDD.ET.LAMBDA], ""))
        return 2 ** (val-1)
        
    network = nx.create_empty_copy(topology)
    colors = {str(k):0 for k in base.demand_vars.keys()}
    
    for k, v in assignment.items():
        if k[0] == base.prefixes[BDD.ET.LAMBDA] and v:
            [l_var, demand_id] = k.split("_")
            colors[demand_id] += power(l_var)
    
    print(colors)
    
    edges = {str(v) : k for k , v in base.edge_vars.items()}
    
    for k, v in assignment.items():
        if k[0] == base.prefixes[BDD.ET.PATH] and v:
            [p_var, demand_id] = k.split("_")
            (source, target, number) = edges[p_var.replace(base.prefixes[BDD.ET.PATH], "")]
            network.add_edge(source, target, label=demand_id, color=color_map[colors[demand_id]])
    
    print(network.edges)
    
    edge_colors = nx.get_edge_attributes(network,'color').values()
    
    # nx.draw(network, edge_color=edge_colors, with_labels=True, node_size = 15, font_size=10)
    # plt.savefig("./assignedGraphs/" + "assigned" + ".png", format="png")
    # plt.close()  
    
    nx.nx_pydot.write_dot(network, "./assignedGraphs/" + "assigned" + ".dot") 
    graphs = pydot.graph_from_dot_file("./assignedGraphs/" + "assigned" + ".dot")   
    if graphs is not None:
        (graph,) = graphs
        graph.write_png("./assignedGraphs/" + "assigned" + ".png")     

    
if __name__ == "__main__":
    color_short_hands = ['red', 'blue', 'green', 'yellow', 'brown', 'black', 'purple', 'lightcyan', 'lightgreen', 'pink', 'lightsalmon', 'lime', 'khaki', 'moccasin', 'olive', 'plum', 'peru', 'tan', 'tan2', 'khaki4', 'indigo']
    color_map = {i : color_short_hands[i] for i in range(len(color_short_hands))}
    
    G = MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/four_node.dot"))
    G = topology.get_nx_graph(topology.TOPZOO_PATH +  "/AI3.gml")
    
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
        
    demands = {0: Demand("A", "B"), 1: Demand("A", "B")}
    demands = topology.get_demands(G, amount=10)
    
    rwa = RWAProblem(G, demands, wavelengths=4)
    assignment = rwa.get_assignments()[0]


    draw_assignment(assignment, rwa.base, G)

