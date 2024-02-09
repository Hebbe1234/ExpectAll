import json
import math
import networkx as nx
import networkx.utils as nxu
from pathlib import Path
import matplotlib.pyplot as plt
import os
from demands import Demand
import random

TOPZOO_PATH = "./topologies/topzoo"

def get_nx_graph(name):
    return nx.MultiDiGraph(nx.read_gml(str(Path(name).resolve()), label='id'))
    
def get_demands(graph: nx.MultiDiGraph, amount: int, offset = 0, seed=10) -> dict[int, Demand]:
    if seed is not None:
        random.seed(seed)

    demands = {}
    
    weight = {s: random.randint(1, 100) for s in graph.nodes()}
    connected = {s: [n for n in list(nx.single_source_shortest_path(graph,s).keys()) if n != s] for s in graph.nodes()}
    connected = {s: v for s,v in connected.items() if len(v) > 0}
    for i  in range(amount):
        source = random.choices(list(connected.keys()), weights=[weight[k] for k in connected.keys()], k=1)[0]
        target = random.choices(connected[source], weights=[weight[k] for k in connected[source]], k=1)[0]

        demands[len(demands)+offset] = Demand(source, target)

    return demands

def get_simple_paths(G: nx.MultiDiGraph, demands, number_of_paths, shortest=False):
    unique_demands = set([(d.source, d.target) for d in demands.values()])
    paths = []
    
    for (s, t) in unique_demands:
        i = 1
        for p in nx.all_simple_edge_paths(G, s, t):
            paths.append(p)
            if i == number_of_paths:
                break     
            
            i += 1
        
        
    return paths

def get_shortest_simple_paths(G: nx.MultiDiGraph, demands, number_of_paths, shortest=False):
    unique_demands = set([(d.source, d.target) for d in demands.values()])
    paths = []
    
    for (s, t) in unique_demands:
        i = 1
        l = 1
        while i < number_of_paths and l < G.number_of_nodes():
            for p in nx.all_simple_edge_paths(G, s, t, l):
                paths.append(p)
                if i == number_of_paths:
                    break     
                
                i += 1
            
            l += 1
            
    return paths

def get_overlapping_simple_paths(G: nx.MultiDiGraph, paths):
    overlapping_paths = []

    for i, path in enumerate(paths):
        for j, other_path in enumerate(paths):
            # check for overlap
            if len(set(path + other_path)) < len(path + other_path):
                overlapping_paths.append((i,j)) 

    return overlapping_paths

def reduce_graph_based_on_demands(G: nx.MultiDiGraph, demands, file_name) -> nx.MultiDiGraph:
    interesting_nodes = set(sum([[demand.source, demand.target] for demand in demands.values()], []))
    old = nx.empty_graph()
    new = nx.MultiDiGraph.copy(G)
    
    while not nxu.graphs_equal(old, new):
        old = nx.MultiDiGraph.copy(new)
        nodes_to_delete = []
        
        for n in new.nodes:
            if n not in interesting_nodes:
                neighbors = list(new.neighbors(n))
                if len(neighbors) <= 1:
                    nodes_to_delete.append(n)

                if len(neighbors) == 2:
                    (i1, o1, i2, o2) = (0,0,0,0)
                    n1 = neighbors[0]
                    n2 = neighbors[1]
                    
                    for e in new.in_edges(n, keys=True):
                        if e[0] == n1:
                            i1 += 1
                        else:
                            i2 += 1
                        
                    
                    for e in new.out_edges(n, keys=True):
                        if e[1] == n1:
                            o1 += 1
                        else:
                            o2 += 1
                    
                    for i in range(min(i1, o2)):
                        new.add_edge(n1, n2)
                    
                    for i in range(min(i2, o1)):
                        new.add_edge(n2, n1)
                    
                    nodes_to_delete.append(n)
                    
        for n in nodes_to_delete:
            new.remove_node(n)

    
    return new
    

def get_all_graphs():
    all_graphs = []
    names = get_all_topzoo_files()
    for name in names : 
        g = get_nx_graph(name)
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

def output_graph_data():
    def get_data(graphs : list[tuple[str, nx.MultiDiGraph]]):
        data = {}
        for n,g in graphs:
            data[n] = {}
            data[n]["edges"] = g.number_of_edges()
            data[n]["nodes"] = g.number_of_nodes()
            data[n]["density"] = nx.density(g)
        
        return data   
            
    graphs = []
    for subdirs, dirs, files in os.walk("./topologies/topzoo"):
        for f in files:
            G = get_nx_graph(subdirs+"/"+f)
            if G.nodes.get("\\n") is not None:
                G.remove_node("\\n")
            graphs.append((f.replace(".gml",""),G))

    data = get_data(graphs)

    with open("topologies/graph_data.json","w") as f:
        data = json.dump(data, f, indent=4)


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
        
