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
  

def get_gravity_demands_no_population(graph: nx.MultiDiGraph, amount: int, seed=10, offset=0, highestuniformthing=7, max_uniform=30, multiplier=1):
    def get_s_and_t_based_on_size(node_to_size, connected):
        total = sum(node_to_size.values())
        # Note that nodes are shuffled before call, so node 16 can have lower probability than node 0.
        nodes = list(node_to_size.keys())
        probability_distribution = [size/total for size in node_to_size.values()]
        while True:
            # Pick k random elements from population list based on the given weights (equal prob if none given)
            source_and_target = random.choices(population=nodes, weights=probability_distribution, k=2)
            source_node = source_and_target[0]
            target_node = source_and_target[1]
            
            if source_node != target_node and target_node in connected[source_node]:
                return source_node, target_node
                
    random.seed(seed)
    
    connected = {s: [n for n in list(nx.single_source_shortest_path(graph,s).keys()) if n != s] for s in graph.nodes()}
    connected = {s: v for s,v in connected.items() if len(v) > 0}
    demands = {}
    
    node_to_size = {}
    increment = (highestuniformthing) / len(connected.keys())
    value = 1
    nodes = []
 
    for n in connected.keys():
        nodes.append(n)
    random.shuffle(nodes)
 
 
    # Dont know if we want to assign sizes to cities in a different way
    for n in nodes:
        node_to_size[n] = value
        value += increment
    
    bound = math.floor(max_uniform / multiplier)
    
    for _ in range(amount):
        s,t = get_s_and_t_based_on_size(node_to_size, connected)
        demand_size = random.choice([(i+1)*multiplier for i in range(0, bound)])
        demands[len(demands)+offset] = Demand(s, t, demand_size)
 
    return demands
    
def get_nodeid_to_population(graph): 
    return {node: data["population"] for node, data in graph.nodes(data=True)}


def get_gravity_demands(graph: nx.MultiDiGraph, amount: int, seed=10, offset=0, max_uniform=30, multiplier=1):
    def get_s_and_t_based_on_size(node_to_size, connected):
        total = sum(node_to_size.values())
        # Note that nodes are shuffled before call, so node 16 can have lower probability than node 0. 
        nodes = list(node_to_size.keys())
        probability_distribution = [round(size/total, 2) for size in node_to_size.values()]
        while True:
            # Pick k random elements from population list based on the given weights (equal prob if none given)
            source_and_target = random.choices(population=nodes, weights=probability_distribution, k=2)
            source_node = source_and_target[0]
            target_node = source_and_target[1]
            
            if source_node != target_node and target_node in connected[source_node]:
                return source_node, target_node
                
    random.seed(seed)
    
    connected = {s: [n for n in list(nx.single_source_shortest_path(graph,s).keys()) if n != s] for s in graph.nodes()}
    connected = {s: v for s,v in connected.items() if len(v) > 0}
    demands = {}
    
    node_to_size = get_nodeid_to_population(graph)
        
    for _ in range(amount): 
        s,t = get_s_and_t_based_on_size(node_to_size, connected)
        demand_size = random.choice(range(1, max_uniform))
        demand_size = math.ceil(demand_size / multiplier) *  multiplier
        demands[len(demands)+offset] = Demand(s, t, demand_size, len(demands)+offset)

    return demands
    

def make_demands_size_n(demands: dict[int,Demand], size): 
    for i,d in demands.items(): 
        d.size = size
    return demands


def d_to_legal_path_dict(demands, paths):
    my_dict = {}
    for ii, d in demands.items(): 
        d_legal_paths = []
        for i,p in enumerate(paths): 
            if p[0][0] == d.source and p[-1][1] == d.target:
                d_legal_paths.append(i)
        my_dict[ii] = d_legal_paths
    return my_dict


def get_channels(demands, number_of_slots, limit=False, cliques=[], clique_limit=False, safe_limit=False):
    max_size = 0
    
    if safe_limit:
        demand_obj = sorted(demands.values(), key=lambda d: d.size * max(d.modulations))[-1]
        max_size = demand_obj.size * max(demand_obj.modulations)
    
    def get_channels_for_demand(number_of_slots, size, max_index):
        channels = []
        
        for i in range(number_of_slots-size+1):
            if (limit or len(cliques) > 0 or safe_limit) and i > max_index:
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
        
        if safe_limit:
            max_index += max_size
            
        for m in demand.modulations:
            demand_channels[d].extend(get_channels_for_demand(number_of_slots, m * demand.size, max_index))
    
    all_channels = []
    
    for channels in demand_channels.values():
        for channel in channels:
            all_channels.append(channel)
    
    return demand_channels

def get_overlapping_channels(demand_channels: dict[int, list[list[int]]]):
    unique_channels = []

    for channels in demand_channels.values():
        for channel in channels:
            if channel not in unique_channels:
                unique_channels.append(channel)
    
    overlapping_channels = []

    # Precompute sets and their lengths
    unique_sets = [set(channel) for channel in unique_channels]
    set_lengths = [len(channel_set) for channel_set in unique_sets]
    num_unique_channels = len(unique_sets)
    # Iterate over unique pairs of channels
    for i in range(num_unique_channels):
        channel_set_i = unique_sets[i]
        length_i = set_lengths[i]
        for j in range(i, num_unique_channels):
            
            length_j = set_lengths[j]
            combined_set_length = length_i + length_j - sum(1 for _ in (channel_set_i & unique_sets[j]))

            if combined_set_length < length_i + length_j:
                overlapping_channels.append((i, j))
                overlapping_channels.append((j, i))
    
    return overlapping_channels, unique_channels

def get_connected_channels(unique_channels):
    channel_to_connected_channels = {i : [] for i,_ in enumerate(unique_channels)}
    
    for i, channel in enumerate(unique_channels):
        for j, other_channel in enumerate(unique_channels):
            # check if starting slot of channel is the slot next to the ending slot  of the other channel
            if channel[0]-1 == other_channel[-1]:
                channel_to_connected_channels[i].append(j)
    return channel_to_connected_channels 
    

def get_disjoint_simple_paths(G: nx.MultiDiGraph, demands, number_of_paths, max_attempts=50):
    unique_demands = set([(d.source, d.target) for d in demands.values()])
    
    paths = []
    for (s, t) in unique_demands:
        demand_paths = []
        i = 1
        G_running = G
        
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
            G.add_edge(edge[0], edge[1], min_edge[0], distance=float(min_edge[1]['distance']) * 10)
        
        yield (G, path)
            
def get_overlapping_simple_paths( paths):
    overlapping_paths = []
    for i, path in enumerate(paths):
        for j, other_path in enumerate(paths):
            # check for overlap
            if len(set(path + other_path)) < len(path + other_path):
                overlapping_paths.append((i,j)) 

    return overlapping_paths

def get_overlap_graph(demands: dict[int,Demand], paths):
    overlapping_paths = get_overlapping_simple_paths(paths)

    overlap_graph = nx.empty_graph()

    # Create a node for each demand    
    for d in demands.keys():
        overlap_graph.add_node(d)

    
    certain_overlap = overlap_graph.copy()
    
    # If two demands overlap, add an edge between them in the overlap grap
    
    for i_d1, d1 in demands.items():
        d1_paths = [i for i, path in enumerate(paths) if path[0][0] == d1.source and path[-1][1] == d1.target]
        for i_d2,d2 in demands.items():
            if i_d1 <= i_d2:
                continue

            has_overlapped = False
            has_certainly_overlapped = True
            
            d2_paths = [i for i, path in enumerate(paths) if path[0][0] == d2.source and path[-1][1] == d2.target]
                        
            for (path1, path2) in product(d1_paths, d2_paths):
                has_certainly_overlapped &= (path1, path2) in overlapping_paths
                if not has_overlapped and (path1, path2) in overlapping_paths:
                    has_overlapped = True
            
            if has_overlapped:
                overlap_graph.add_edge(i_d1, i_d2)
            if has_certainly_overlapped:
                certain_overlap.add_edge(i_d1, i_d2)
    
    return overlap_graph, certain_overlap

def get_safe_upperbound(demands: dict[int,Demand], paths, max_slots: int):
    if len(demands) == 1:
        return max([m * demands[0].size for m in demands[0].modulations])
    
    overlap_graph, _ = get_overlap_graph(demands, paths)
    connected_components = list(nx.connected_components(overlap_graph))
    upperbound = 0 
    for component in connected_components: 
        _sum = 0
        for node in component: 
            _sum += max([m * demands[node].size for m in demands[node].modulations])
        if _sum > upperbound : 
            upperbound = _sum

    return min(upperbound, max_slots)


def get_overlap_cliques(demands: dict[int,Demand], paths):
    
    overlap_graph, _ = get_overlap_graph(demands, paths)
    
    # draw_graph(certain_overlap, "overlap_graph")
        
    return list(nx.clique.find_cliques_recursive(overlap_graph))

   
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

if __name__ == "__main__":
    pass