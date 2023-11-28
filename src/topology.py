import math
import networkx as nx
from pathlib import Path
import matplotlib.pyplot as plt
import os
from demands import Demand
import random

TOPZOO_PATH = "./topologies/topzoo"

def get_nx_graph(name):
    return nx.MultiDiGraph(nx.read_gml(str(Path(name).resolve()), label='id'))
    
def get_demands(graph: nx.MultiDiGraph, amount: int, seed=10) -> dict[int, Demand]:
    if seed is not None:
        random.seed(seed)

    demands = {}
    
    weight = {s: random.randint(1, 100) for s in graph.nodes()}
    connected = {s: [n for n in list(nx.single_source_shortest_path(graph,s).keys()) if n != s] for s in graph.nodes()}
    connected = {s: v for s,v in connected.items() if len(v) > 0}
    for i  in range(amount):
        source = random.choices(list(connected.keys()), weights=[weight[k] for k in connected.keys()], k=1)[0]
        target = random.choices(connected[source], weights=[weight[k] for k in connected[source]], k=1)[0]

        demands[len(demands)+1] = Demand(source, target)

    return demands

def get_all_graphs():
    all_graphs = []
    names = get_all_topzoo_files()
    for name in names : 
        g = get_nx_graph(name)
        # largest_cc = max(nx.connected_components(g.to_undirected()), key=len)
   
        # diameter = 0
        # ccs = nx.connected_components(g.to_undirected())
        # for cc in ccs:
        #     gcc = nx.induced_subgraph(g, cc)
        #     diameter = max(diameter, nx.diameter(gcc))
        
        # print(len(g.nodes), len(largest_cc),diameter, math.ceil(math.log2(len(g.edges)))*len(largest_cc),  len(g.edges()), name)
        
        all_graphs.append(g)
    return all_graphs
    
def get_all_topzoo_files():
    topfiles = []

    for entry in os.scandir(TOPZOO_PATH):
        if entry.path.endswith(".gml") and entry.is_file():
            topfiles.append(entry.path)
    return topfiles

def draw_graph(graph, file_name): 
    nx.draw(graph, with_labels=True, node_size = 15, font_size=10)
    plt.savefig("./drawnGraphs/" + file_name + ".svg", format="svg")
    plt.close()

def main():
    all_graphs = get_all_graphs()
    for g in all_graphs:
        num_nodes = g.number_of_nodes()
        num_edges = g.number_of_edges()
        if num_nodes < 30: 
            print(f'Graph Label: {g.graph["label"]}')
            print(f'Number of Nodes: {num_nodes}')
            print(f'Number of Edges: {num_edges}')


if __name__ == "__main__":
    main()
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/simple_net.dot"))
    G = get_nx_graph(TOPZOO_PATH +  "\\Aarnet.gml")

    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
        
    # print(get_demands(G, 200))