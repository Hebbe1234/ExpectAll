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

def add_distances_to_gmls():
    topfiles = []

    for entry in os.scandir(TOPZOO_PATH):
        MAP_SIZE = 500
        g = nx.MultiDiGraph(nx.read_gml(str(Path(entry).resolve()), label='id'))
        fixed_positions = {n[0]: (n[1].get("Longitude"), n[1].get("Latitude")) for n in g.nodes(data=True)}
        fixed_positions = {k: (((MAP_SIZE/360)* (MAP_SIZE + v[0])),((100/180)* (90 - v[1]))) for k, v in fixed_positions.items() if v[0] is not None and v[1] is not None}
        
        pos = None
        
        pos = nx.spring_layout(g)

        distances = {}
        
        for edge in g.edges(keys=True):
            s_node = edge[0]
            t_node = edge[1]
            s_x = pos[s_node][0]    
            s_y = pos[s_node][1]    
            t_x = pos[t_node][0]    
            t_y = pos[t_node][0]    

            distances[edge] = math.sqrt(math.pow((s_x-t_x),2) + math.pow((s_y - t_y), 2))

        nx.set_edge_attributes(g, distances, "distance")
        nx.write_gml(g, str(Path(entry).resolve()).replace("topzoo", "topzoo_with_distances"))
        
        print(entry)
        nx.draw(g,pos, with_labels=True, node_size = 15, font_size=10)
        plt.savefig("./drawnGraphs_with_distances/" + str(Path(entry).resolve()).split("\\")[-1].replace(".gml", "") + ".svg", format="svg")
        plt.close()
  

def get_gravity_demands2_very_random(graph: nx.MultiDiGraph, amount: int, seed=10, offset = 0, highestuniformthing = 7):
    random.seed(seed)

    connected = {s: [n for n in list(nx.single_source_shortest_path(graph,s).keys()) if n != s] for s in graph.nodes()}
    connected = {s: v for s,v in connected.items() if len(v) > 0}
    demands = {}
    

    for _ in range(amount): 
        s,t = get_random_s_and_t(graph.nodes(), connected)
        demand_size = random.randrange(1, highestuniformthing+1) * random.randrange(1, highestuniformthing+1)
        demands[len(demands)+offset] = Demand(str(s), str(t), demand_size)

    return demands

def get_random_s_and_t(nodes, connected): 
    while True: 
        n1 = random.randrange(0, len(nodes))
        n2 = random.randrange(0, len(nodes))
        if n1 != n2 :
            n1connected = connected[n1]
            if n2 in n1connected:
                return n1,n2

def get_gravity_demands2_nodes_have_constant_size(graph: nx.MultiDiGraph, amount: int, seed=10, offset = 0, highestuniformthing = 7):
    random.seed(seed)
    
    connected = {s: [n for n in list(nx.single_source_shortest_path(graph,s).keys()) if n != s] for s in graph.nodes()}
    connected = {s: v for s,v in connected.items() if len(v) > 0}
    demands = {}

    node_to_size = {}
    increment = (highestuniformthing) / len(graph.nodes)
    value = 1
    nodes = []

    for n in graph.nodes(): 
        nodes.append(n)

    random.shuffle(nodes)

    for n in nodes: 
        node_to_size[n] = value
        value += increment

    

    for _ in range(amount): 
        s,t = get_random_s_and_t(graph.nodes(), connected)
        demand_size = round(node_to_size[s] * node_to_size[t])
        demands[len(demands)+offset] = Demand(s, t, demand_size)

    return demands

# excellent :)
def get_gravity_demands(graph: nx.MultiDiGraph, amount: int, seed=10, offset = 0,):
    def pop_func(x:float):
        return (10*(10**8))/(1+0.5*(10**8)*(math.e**(-0.016*(x-500))))
    def bandwidth_to_slots_func(bandwidth, slot_size=12.5):
        return ((1/30)*bandwidth + 2/3)*(12.5/slot_size)
    def slot_func(x:float,slot_size=12.5):
        bandwidth = x*(2*10**(-4)) #average american bandwidth Gbps

        return math.ceil(bandwidth_to_slots_func(bandwidth,slot_size))

    random.seed(seed)
    demands = {}
    connected = {s: [n for n in list(nx.single_source_shortest_path(graph,s).keys()) if n != s] for s in graph.nodes()}
    connected = {s: v for s,v in connected.items() if len(v) > 0}

    chunk_size = 1100/graph.number_of_nodes()
    weight = {s: pop_func(random.randint(math.floor(i*chunk_size), math.floor((i+1)*chunk_size)))/100 for i,s in enumerate(graph.nodes())}

    #weight = {s: pop_func(random.randint(0, 1100)) / 100 for s in graph.nodes()}
    
    for s in graph.nodes():
        if s not in connected:
            continue
        for t in graph.nodes():
            if t not in connected[s]:
                continue
            demands[len(demands)+offset] = Demand(s, t,slot_func(weight[s]*weight[t]))
    
    return {j+offset: d for j, (i,d) in enumerate(sorted(demands.items(), key=lambda item: item[1].size, reverse=True)[:min(amount,len(demands))])}
    
def get_demands_size_x(graph: nx.MultiDiGraph, amount:int, seed=10, offset=0, size=1):
    demands = get_gravity_demands(graph, amount, seed, offset)
    
    for demand in demands.keys():
        demands[demand].size = size
    
    return demands

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

        demands[len(demands)+offset] = Demand(source, target,1)

    return demands


def get_simple_paths(G: nx.MultiDiGraph, demands, number_of_paths, shortest=False):
    unique_demands = set([(d.source, d.target) for d in demands.values()])
    paths = []
    for (s, t) in unique_demands:
        i = 0
        for p in nx.all_simple_edge_paths(G, s, t):
            paths.append(p)
            i += 1
            if i == number_of_paths:
                break     
        
    return paths

def d_to_legal_path_dict(demands, paths):
    my_dict = {}
    for ii, d in demands.items(): 
        d_legal_paths = []
        for i,p in enumerate(paths): 
            if p[0][0] == d.source and p[-1][1] == d.target:
                d_legal_paths.append(i)
        my_dict[ii] = d_legal_paths
    return my_dict


def get_channels(demands, number_of_slots, limit=False, cliques=[], clique_limit=False):
    def get_channels_for_demand(number_of_slots, size, max_index):
        channels = []
        
        for i in range(number_of_slots-size+1):
            if (limit or len(cliques) > 0) and i > max_index:
                break
            channel = []
            for j in range(i, i + size):
                channel.append(j)
            
            channels.append(channel)
                
            
        return channels
    
    demand_channels = {d:[] for d in demands.keys()}
    
    max_slot = {d: sum([max(demand.modulations) * demand.size for j, demand in demands.items() if d > j])  for d, demand in demands.items()}
    if len(cliques) > 0:
        max_slot = {
            d:min(max([sum([demands[cd].size * max(demands[cd].modulations) for cd in c if cd != d]) for c in cliques if d in c]), max_slot[d]) for d in demands
        }

        if clique_limit:
            sorted_cliques = sorted(cliques, key=lambda c: len(c))
            demand_to_number_of_cliques = {d: len([c for c in sorted_cliques if d in c]) for d in demands}
            
            max_slot = {d:max_slot[d] for d in demands}
            
            for c in sorted_cliques:
                sorted_clique = sorted(c, key=lambda d: demand_to_number_of_cliques[d])
                current_index = 0
                
                for d in sorted_clique:
                    max_slot[d] = current_index
                    current_index += max(demands[d].modulations) * demands[d].size
                
                        
    for d, demand in demands.items():
        max_index = max_slot[d]
        for m in demand.modulations:
            demand_channels[d].extend(get_channels_for_demand(number_of_slots, m * demand.size, max_index))
    
    return demand_channels

def get_overlapping_channels(demand_channels: dict[int, list[list[int]]]):
    unique_channels = []
    for channels in demand_channels.values():
        for channel in channels:
            if channel not in unique_channels:
                unique_channels.append(channel)
    
    overlapping_channels = []

    for i, channel in enumerate(unique_channels):
        for j, other_channel in enumerate(unique_channels):
            #Very slow
            if len(channel + other_channel) > len(set(channel + other_channel)):
                overlapping_channels.append((i, j))
          
    return overlapping_channels, unique_channels

def get_connected_channels(unique_channels):
    channel_to_connected_channels = {i : [] for i,_ in enumerate(unique_channels)}
    
    for i, channel in enumerate(unique_channels):
        for j, other_channel in enumerate(unique_channels):
            # check if starting slot of channel is the slot next to the ending slot  of the other channel
            if channel[0]-1 == other_channel[-1]:
                channel_to_connected_channels[i].append(j)
    return channel_to_connected_channels 
    


def get_shortest_simple_paths(G: nx.MultiDiGraph, demands, number_of_paths, shortest=False):
    unique_demands = set([(d.source, d.target) for d in demands.values()])
    paths = []
    
    for (s, t) in unique_demands:
        i = 0
        l = 1
        d_paths = []
        while i < number_of_paths and l < G.number_of_nodes():
            for p in nx.all_simple_edge_paths(G, s, t, l):
                d_paths.append(p)
                i += 1
                if i == number_of_paths:
                    paths.extend(d_paths)
                    break     
                    
            d_paths = []
            if l + 1 == G.number_of_nodes():
                paths.extend(d_paths)

            l += 1
            
    return paths

def get_disjoint_simple_paths(G: nx.MultiDiGraph, demands, number_of_paths, max_attempts=50):
    unique_demands = set([(d.source, d.target) for d in demands.values()])
    
    paths = []
    G_running = G
    for (s, t) in unique_demands:
        demand_paths = []
        i = 1
        for (G_new, path) in dijkstra_generator(G_running, s, t):
            G_running = G_new.copy()
            # print(G_running.edges(data="distance"))
            # print("###")
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
    for edge in G.edges(keys=True, data='distance', default=1):
        G.add_edge(edge[0], edge[1], edge[2],distance=edge[3])
    
    while True:
        
        dijkstra_path = nx.dijkstra_path(G, s, t, weight='distance')
        edges = list(nxu.pairwise(dijkstra_path))
        path = []
        
        for edge in edges:
            min_edge = min(G.get_edge_data(edge[0], edge[1]).items(), key=lambda x: x[1]['distance'])
            path.append((edge[0], edge[1], min_edge[0]))
            G.add_edge(edge[0], edge[1], min_edge[0], distance=min_edge[1]['distance'] * 10)
        
        yield (G, path)
            
def get_overlapping_simple_paths( paths):
    overlapping_paths = []
    for i, path in enumerate(paths):
        for j, other_path in enumerate(paths):
            # check for overlap
            if len(set(path + other_path)) < len(path + other_path):
                overlapping_paths.append((i,j)) 

    return overlapping_paths

def get_overlapping_simple_paths_with_index(paths):
    overlapping_paths = []
    for i, path in (paths):
        for j, other_path in (paths):
            # check for overlap
            if len(set(path + other_path)) < len(path + other_path):
                overlapping_paths.append((i,j)) 

    return overlapping_paths

def get_overlap_cliques(demands: list[Demand], paths):
    
    overlapping_paths = get_overlapping_simple_paths(paths)

    overlap_graph = nx.empty_graph()

    demand_to_node = {}
    
    # Create a node for each demand    
    for d in demands:
        overlap_graph.add_node(len(demand_to_node.values()))
        demand_to_node[d] = len(demand_to_node.values())
    
    certain_overlap = overlap_graph.copy()
    
    # If two demands overlap, add an edge between them in the overlap grap
    for i_d1, d1 in enumerate(demands):
        d1_paths = [i for i, path in enumerate(paths) if path[0][0] == d1.source and path[-1][1] == d1.target]
        for d2 in demands[i_d1+1:]:
            has_overlapped = False
            has_certainly_overlapped = True
            
            d2_paths = [i for i, path in enumerate(paths) if path[0][0] == d2.source and path[-1][1] == d2.target]
                        
            for (path1, path2) in product(d1_paths, d2_paths):
                has_certainly_overlapped &= (path1, path2) in overlapping_paths
                if (path1, path2) in overlapping_paths:
                    has_overlapped = True
                    break
            
            if has_overlapped:
                overlap_graph.add_edge(demand_to_node[d1], demand_to_node[d2])
            if has_certainly_overlapped:
                certain_overlap.add_edge(demand_to_node[d1], demand_to_node[d2])
    
    # draw_graph(certain_overlap, "overlap_graph")
        
    reduced_cliques = list(nx.clique.find_cliques_recursive(overlap_graph))
    return reduced_cliques

def reduce_graph_based_on_demands(G: nx.MultiDiGraph, demands) -> nx.MultiDiGraph:
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
    
def reduce_graph_based_on_paths(G: nx.MultiDiGraph, paths) -> nx.MultiDiGraph:
    new = nx.MultiDiGraph.copy(G)
    
    interesting_edges = []
    for p in paths:
        for e in p:
            interesting_edges.append(e)
    
    interesting_edges = set(interesting_edges)
    
    edges_to_remove = [e for e in G.edges(keys=True) if e not in interesting_edges]
    for e in edges_to_remove:
        new.remove_edge(e[0], e[1], key=e[2])
    
    nodes_to_delete = []
    for n in new.nodes:
        if len(new.edges(n)) == 0:
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



def split_into_multiple_graphs(graph):
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

            dSource = Demand(demand.source, removedNode, demand.size)
            dTarget = Demand(removedNode,demand.target, demand.size)

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

def split_paths(graphs, removedNode, paths: list[list[tuple]]):
    graphToNewPaths:dict[nx.MultiDiGraph, list[tuple]] = {}

    for g in graphs: 
        pathForCurrentGraph = []
        for index, path in enumerate(paths):
            startNode = path[0][0]
            endNode  = path[-1][1]

            if startNode in g.nodes and endNode in g.nodes: 
                pathForCurrentGraph.append((index,path))

            elif startNode in g.nodes and startNode != removedNode:
                indexOfNode = -1
                for i,(s,t,_) in enumerate(path):  #Potential error
                    if t == removedNode: 
                        indexOfNode = i
                        break
                if indexOfNode == -1:
                    print("Hs")
                    exit()
                newPath = path[0:indexOfNode+1]
                pathForCurrentGraph.append((index,newPath))

            elif endNode in g.nodes and endNode != removedNode:
                indexOfNode = -1
                for i,(s,t,_) in enumerate(path):  #Potential error
                    if s == removedNode: 
                        indexOfNode = i
                        break
                if indexOfNode == -1:
                    print("H")
                    print(removedNode)
                    print(g.nodes)
                    print(path)
                    exit()
                newPath = path[indexOfNode:]
                pathForCurrentGraph.append((index,newPath))
        
        graphToNewPaths[g] = pathForCurrentGraph

    return graphToNewPaths        




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

            dSource = Demand(demand.source, removedNode, demand.size)
            dTarget = Demand(removedNode,demand.target, demand.size)


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

def get_demand_sizes_in_order(demands): 
    demands = sorted(demands.items(), key=lambda item: item[1].size, reverse=False)
    csv = []
    for i,d in enumerate(demands): 
        csv.append(d[1].size)
    return csv

if __name__ == "__main__":
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/split5NodeExample.dot"))
    G = get_nx_graph(TOPZOO_PATH +  "/Ai3.gml")

    demands = get_gravity_demands2_nodes_have_constant_size(G, 10000, 0, 0, 7)
    demands = sorted(demands.items(), key=lambda item: item[1].size, reverse=False)
    print(get_demand_sizes_in_order(demands))
    # if G.nodes.get("\\n") is not None:
    #     G.remove_node("\\n")
    
    # demands = get_demands(G,8)
    # paths = get_disjoint_simple_paths(G, demands, 2)
    # nx.draw(G, with_labels=True, node_size = 15, font_size=10)
    # plt.savefig("./reducedDrawnGraphs/" + "edges_pruned_before" + ".svg", format="svg")
    # plt.close()
    
    # newG = reduce_graph_based_on_paths(G, paths)
    
    # nx.draw(newG, with_labels=True, node_size = 15, font_size=10)
    # plt.savefig("./reducedDrawnGraphs/" + "edges_pruned_after" + ".svg", format="svg")
    # plt.close()
    
    # print(len(G.nodes), len(newG.nodes))
    # print(len(G.edges(keys=True)), len(newG.edges(keys=True)))