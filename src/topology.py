from itertools import product
import json
import math
import networkx as nx
import networkx.utils as nxu
from pathlib import Path
import matplotlib.pyplot as plt
import os
from demands import Demand
import random
import time

TOPZOO_PATH = "./topologies/topzoo"

def get_nx_graph(name):
    return nx.MultiDiGraph(nx.read_gml(str(Path(name).resolve()), label='id'))
    

#best in 'preliminary' testing 
def demands_reorder_stepwise_similar_first(G: nx.MultiGraph, demands):
    new_demands = {}
    newly_added_demmands = []

    for i,d in demands.items():
        for j,dd in demands.items():
            if i == j:
                continue
            if d.source == dd.source and d.target == dd.target and [i,j] not in newly_added_demmands:
                new_demands.update({i:d, j:dd})
                newly_added_demmands.extend([i,j])
    
    for i,d in demands.items():
        for j,dd in demands.items():
            if i == j:
                continue
            if d.source == dd.source and [i,j] not in newly_added_demmands:
                new_demands.update({i:d, j:dd})
                newly_added_demmands.extend([i,j])


    for i,d in demands.items():                 
        for j,dd in demands.items():
            if i == j:
                continue
            if d.target == dd.target and i not in newly_added_demmands:
                new_demands.update({i:d, j:dd})
                newly_added_demmands.extend([i,j])

    for i,d in demands.items():                 
        if i not in newly_added_demmands:
            new_demands.update({i:d})            
            newly_added_demmands.append(i)

    assert len(new_demands) == len(demands)

    return new_demands
	            



def edge_balance_heuristic(demands, graph: nx.MultiDiGraph):
    demandSetsSource = {node_s: get_demand_set(demands, node_s) for node_s in graph.nodes}
    demandSetsTarget = {node_t : get_demand_set(demands, node_t, isSource=False) for node_t in graph.nodes}
    print(demandSetsSource)
    print(demandSetsTarget)
    
    sorting_list = []
    
    for (source_node, sourceSet), (target_node, targetSet) in zip(demandSetsSource.items(), demandSetsTarget.items()):
        source_balance = math.ceil(len(sourceSet)/len(graph.out_edges(source_node)))
        target_balance = math.ceil(len(targetSet)/len(graph.in_edges(target_node)))
        
        sorting_list.extend([(sourceSet, source_balance), (targetSet, target_balance)])   
    
    sorting_list.sort(key=lambda tuple: tuple[1], reverse=True) # tuple[1] = balance
    new_demands = {}

    for (demand_set, _) in sorting_list:
        for demand_id in demand_set:
            if demand_id not in new_demands:
                new_demands[demand_id] = demands[demand_id] 
    
    print("Minimal number of wavelengths: ", sorting_list[0][1])
    return new_demands

def get_demand_set(demands, node, isSource=True):
    if isSource:
        return [demand_id for demand_id, demand in demands.items() if demand.source == node]
    
    return [demand_id for demand_id, demand in demands.items() if demand.target == node]

def reorder_demands(graph, demands, descending=False) -> tuple[dict[int, Demand], dict[int, tuple[list, list]]]:
    demand_sharing_points = [(0, i, [], []) for i, _ in demands.items()]
    
    for i, d in demands.items():
        for i_prime, d_prime in demands.items():
            (points, d_id, source_ds, target_ds) = demand_sharing_points[i]

            if d.source == d_prime.source and len(graph.out_edges(d.source)) == 1:
                source_ds.append(i_prime)
                demand_sharing_points[i] = (points+1, d_id, source_ds, target_ds)
                continue
            
            if d.target == d_prime.target and len(graph.in_edges(d.target)) == 1:
                target_ds.append(i_prime)
                demand_sharing_points[i] = (points+1, d_id, source_ds, target_ds)
    
    demand_sharing_points.sort(key=lambda x: max(len(x[2]),len(x[3])), reverse=descending)        
    
    return ({i : demands[i] for j, (_, i, _, _) in enumerate(demand_sharing_points)}, {i:(ds,tds) for (_,i,ds,tds) in demand_sharing_points}) 

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

def order_demands_based_on_shortest_path(G: nx.MultiDiGraph, demands, shortest_first = False):
    paths = get_shortest_simple_paths(G, demands, 1)
    demand_to_path_length = []
    for i,d in demands.items():
        for path in paths:
            if d.source == path[0][0] and d.target == path[-1][1]:
                demand_to_path_length.append((d, len(path)))
    
    new_demands = []   
    if shortest_first:
        new_demands = sorted(demand_to_path_length, key=lambda x:x[1])
    else:
        new_demands = sorted(demand_to_path_length, key=lambda x:x[1])
        new_demands.reverse()

    new_demands = {i:demand for i, (demand,_) in enumerate(new_demands)}

    return new_demands

                
            
    
    

def get_shortest_simple_paths(G: nx.MultiDiGraph, demands, number_of_paths, shortest=False):
    unique_demands = set([(d.source, d.target) for d in demands.values()])
    paths = []
    
    for (s, t) in unique_demands:
        i = 0
        l = 1
        while i < number_of_paths and l < G.number_of_nodes():
            for p in nx.all_simple_edge_paths(G, s, t, l):
                paths.append(p)
                i += 1
                if i == number_of_paths:
                    break     
                
            
            l += 1
            
    return paths

def get_disjoint_simple_paths(G: nx.MultiDiGraph, demands, number_of_paths, max_attempts=50):
    unique_demands = set([(d.source, d.target) for d in demands.values()])
    
    paths = []
    
    for (s, t) in unique_demands:
        demand_paths = []
        i = 1
        for path in dijkstra_generator(G, s, t):
            if path not in demand_paths:
                demand_paths.append(path)
            else:
                i = i + 1
                
            if len(demand_paths) == number_of_paths or i > max_attempts:
                paths.extend(demand_paths)
                break     
        
    
            
    return paths

def dijkstra_generator(G: nx.MultiDiGraph, s, t):
    G = G.copy()
    
    for edge in G.edges(keys=True):
        G.add_edge(edge[0], edge[1], edge[2], weight=1)
    
    while True:
        dijkstra_path = nx.dijkstra_path(G, s, t, weight='weight')
        edges = list(nxu.pairwise(dijkstra_path))
        path = []
        
        for edge in edges:
            min_edge = min(G.get_edge_data(edge[0], edge[1]).items(), key=lambda x: x[1]['weight'])
            path.append((edge[0], edge[1], min_edge[0]))
            G.add_edge(edge[0], edge[1], min_edge[0], weight=min_edge[1]['weight'] * 10)
        
        yield path
            
def get_overlapping_simple_paths( paths):
    overlapping_paths = []
    for i, path in enumerate(paths):
        for j, other_path in enumerate(paths):
            # check for overlap
            if len(set(path + other_path)) < len(path + other_path):
                overlapping_paths.append((i,j)) 

    return overlapping_paths

def get_overlap_cliques(demands: list[Demand], paths):
    overlapping_paths = get_overlapping_simple_paths(paths)
    print((overlapping_paths))
    non_overlap_graph = nx.empty_graph()

    demand_to_node = {}
    
    for d in demands:
        non_overlap_graph.add_node(len(demand_to_node.values()))
        demand_to_node[d] = len(demand_to_node.values())

    for i_d1, d1 in enumerate(demands):
        d1_paths = [i for i, path in enumerate(paths) if path[0][0] == d1.source and path[-1][1] == d1.target]
        has_overlapped = False
        # print(i_d1)
        for d2 in demands[i_d1+1:]:
            d2_paths = [i for i, path in enumerate(paths) if path[0][0] == d2.source and path[-1][1] == d2.target]
            
            for path1, path2 in product(d1_paths, d2_paths):
                # print(path1, path2)
                if (path1, path2) in overlapping_paths:
                    has_overlapped = True
                    break
            
            if has_overlapped:
                non_overlap_graph.add_edge(demand_to_node[d1], demand_to_node[d2])
        
    cliques = list(nx.clique.enumerate_all_cliques(non_overlap_graph))
    reduced_cliques = []
    
    for c in cliques:
        found = False
        for c2 in cliques:
            if len(c) < len(c2) and set(c).issubset(set(c2)):
                found = True
        
        if not found:
            reduced_cliques.append(c)      
    
    for rc in reduced_cliques:
        print(rc)
    
    return reduced_cliques

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


def find_node_to_minimize_largest_component(graph : nx.MultiGraph):
    min_max_component_size = float('inf')
    node_to_remove = None
    graph = graph.to_undirected()
    for node in graph.nodes():
        # Make a copy of the graph and remove the current node
        temp_graph = graph.copy()
        temp_graph.remove_node(node)

        # Check if the graph is connected
        if not nx.is_connected(temp_graph):
            # Calculate the size of the largest connected component
            connected_components = list(nx.connected_components(temp_graph))
            max_component_size = max(len(component) for component in connected_components)
            # Update the minimum size of the largest connected component and the corresponding node
            if max_component_size < min_max_component_size:
                min_max_component_size = max_component_size
                node_to_remove = node
    if node_to_remove == None:
        return None
    if min_max_component_size < 0.70*len(graph.nodes()): 
        return node_to_remove
    return None



def split_into_multiple_graphs(graph = None):
    if graph == None: 
        graph = get_nx_graph(TOPZOO_PATH +  "/Bren.gml")
    bestNodeToRemove = find_node_to_minimize_largest_component(graph)
    if bestNodeToRemove is None: 
        return None, None
    temp_graph = graph.copy()
    temp_graph.remove_node(bestNodeToRemove)
    connected_components = nx.connected_components(temp_graph.to_undirected())
    smallerGraphs = []
    for c in connected_components:
        k = set(c) | {bestNodeToRemove}
        smallerGraphs.append(graph.subgraph(k))
    return smallerGraphs, bestNodeToRemove

def find_node_in_graphs(graphs, node):
    res = [g for g in graphs if node in g.nodes()]
    return res[0]

def split_demands(G, graphs, removedNode, demands:dict[int,Demand]):
    newDemandsDict:dict[int,Demand] = {}
    oldDemandsToNewDemands:dict[int,list[int]] = {}
    graphToNewDemands = {}

    # demandDict = {}
    # graphToDemandIdDict = {}
    newDemandIndex = 0
    for index, demand in demands.items():
        sourcegraph = find_node_in_graphs(graphs, demand.source)
        targetgraph = find_node_in_graphs(graphs, demand.target)

        if demand.source == removedNode:
            sourcegraph = targetgraph
        elif demand.target == removedNode:
            targetgraph = sourcegraph
        
        if sourcegraph == targetgraph: 
            #NewdemandDict
            newDemandsDict[newDemandIndex] = demand

            #oldDemandTONewDemandDict
            if index in oldDemandsToNewDemands : 
                oldDemandsToNewDemands[index].append(newDemandIndex)
            else: 
                oldDemandsToNewDemands[index] = [newDemandIndex]

            #GraphToNewDmeandsDict
            if sourcegraph in graphToNewDemands : 
                graphToNewDemands[sourcegraph].append(newDemandIndex)
            else: 
                graphToNewDemands[sourcegraph] = [newDemandIndex]

            newDemandIndex += 1

        else : 

            dSource = Demand(demand.source, removedNode)
            dTarget = Demand(removedNode,demand.target)

            newDemandsDict[newDemandIndex] = dSource
            newDemandsDict[newDemandIndex+1] = dTarget

            #oldDemandTONewDemandDict
            if index in oldDemandsToNewDemands : 
                oldDemandsToNewDemands[index].append(newDemandIndex)
                oldDemandsToNewDemands[index].append(newDemandIndex+1)
            else: 
                oldDemandsToNewDemands[index] = [newDemandIndex, newDemandIndex+1]

            #GraphToNewDmeandsDict
            if sourcegraph in graphToNewDemands : 
                graphToNewDemands[sourcegraph].append(newDemandIndex)
            else: 
                graphToNewDemands[sourcegraph] = [newDemandIndex]

            if targetgraph in graphToNewDemands : 
                graphToNewDemands[targetgraph].append(newDemandIndex+1)
            else: 
                graphToNewDemands[targetgraph] = [newDemandIndex+1]
            newDemandIndex += 2
                



    return newDemandsDict, oldDemandsToNewDemands, graphToNewDemands




def split_demands2(G, graphs, removedNode, demands:dict[int,Demand]):
    graphToNewDemands:dict[nx.MultiDiGraph, dict[int,Demand]] = {}

    for index, demand in demands.items():
        sourcegraph = find_node_in_graphs(graphs, demand.source)
        targetgraph = find_node_in_graphs(graphs, demand.target)

        if demand.source == removedNode:
            sourcegraph = targetgraph
        elif demand.target == removedNode:
            targetgraph = sourcegraph
        
        if sourcegraph == targetgraph: 
            #GraphToNewDmeandsDict

            if sourcegraph in graphToNewDemands : 
                graphToNewDemands[sourcegraph].update({index: demand})
            else: 
                graphToNewDemands[sourcegraph] = {index: demand}

        else : 

            dSource = Demand(demand.source, removedNode)
            dTarget = Demand(removedNode,demand.target)


            #GraphToNewDmeandsDict
            if sourcegraph in graphToNewDemands : 
                graphToNewDemands[sourcegraph].update({index: dSource})
            else: 
                graphToNewDemands[sourcegraph] = {index: dSource}

            if targetgraph in graphToNewDemands : 
                graphToNewDemands[targetgraph].update({index: dTarget})
            else: 
                graphToNewDemands[targetgraph] = {index: dTarget}
                


    return graphToNewDemands


def main():
    pass
    #order_demands_based_on_shortest_path()
    
    # all_graphs = get_all_graphs()
    # names = get_all_topzoo_files()
    # j = 0
    # for i in range(len(all_graphs)):
    #     if find_node_to_minimize_largest_component(all_graphs[i]) != None:
    #         j+= 1
    #         print(names[i], j)
        # num_nodes = g.number_of_nodes()
        # num_edges = g.number_of_edges()
        # if num_nodes < 30: 
        #     print(f'Graph Label: {g.graph["label"]}')
        #     print(f'Number of Nodes: {num_nodes}')
        #     print(f'Number of Edges: {num_edges}')

if __name__ == "__main__":
    #split_into_multiple_graphs()
    main()
    exit()
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/simple_net.dot"))
    G = get_nx_graph(TOPZOO_PATH +  "\\Aarnet.gml")

    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
        
