import topology
from demands import Demand
import random
from numpy import array_split
import networkx as nx

# evenly splits demands into n buckets based on order
def get_buckets_naive(demands:dict[int,Demand], max_buckets=5):
    d_ids = list(demands.keys())
    return [list(a) for a in array_split(d_ids, min(max_buckets,len(d_ids)))]


def __assign_buckets_based_on_graph(demands, visited_demands, buckets, overlapping_graph, use_max=False):
    #for each demand, choose the bucket that has the most number of overlaps on the demands that are already there
    for demand in demands:
        if demand in visited_demands:
            continue
        visited_demands.add(demand)

        current_overlaps_in_buckets = {i:0 for i in range(len(buckets))}

        #find number of overlaps with demands in each bucket
        for b_id,bucket in enumerate(buckets):
            neighbors = set(overlapping_graph.neighbors(demand))
            current_overlaps_in_buckets[b_id] = len([d for d in bucket if d in neighbors]) 
        
        # best bucket defined by having the most amount of overlaps with current demand or least amount
        best_bucket_overlap = max(current_overlaps_in_buckets.values()) if use_max else min(current_overlaps_in_buckets.values())
        choices = [b_id for b_id,overlap_count in current_overlaps_in_buckets.items() if overlap_count == best_bucket_overlap]
        
        #for tie breakers, choose smallest bucket
        smallest_bucket_size = min([len(buckets[b_id]) for b_id in choices])
        choice = [b_id for b_id in choices if len(buckets[b_id]) == smallest_bucket_size][0]

        buckets[choice].add(demand)

    return buckets


def get_buckets_bridge_node(demands: dict[int,Demand], G: nx.MultiDiGraph, paths=[]):
    sub_graphs, _ = topology.split_into_multiple_graphs(G)
    if sub_graphs is None:
        return []
    
    buckets = [[] for g in sub_graphs]
    bucket_to_overlaps = {i:[] for i,_ in enumerate(buckets)}
    
    for split_id, g in enumerate(sub_graphs):
        for di, d in demands.items():
            if d.source in g.nodes() or d.target in g.nodes():
                buckets[split_id].append(di)
                    
        for i, path in enumerate(paths):
            for j, other_path in enumerate(paths):
                # check for overlap
                path = set(path)
                other_path = set(other_path)
                overlapping_edges = path.intersection(other_path)
                if len(overlapping_edges) > 0 and len(set(g.edges) - overlapping_edges) < len(g.edges):
                    bucket_to_overlaps[split_id].append((i,j))



    return [b for b in buckets if b != []], bucket_to_overlaps

# Split demands such that demands that overlap on any path are put in seperate buckets
def get_buckets_overlapping_graph(demands: list[int], overlapping_graph : nx.Graph, certain_overlap_graph :nx.Graph, max_buckets=5):
    buckets = [set() for i in range(min(len(demands),max_buckets))]
    visited_demands = set()
    demands_with_certain_overlap = [d for d in demands if len(list(certain_overlap_graph.neighbors(d))) > 0]

    buckets = __assign_buckets_based_on_graph(demands_with_certain_overlap, visited_demands, buckets, certain_overlap_graph)
    buckets = __assign_buckets_based_on_graph(demands, visited_demands,buckets, overlapping_graph)
    return buckets


# Split demands such that demands that overlap on any path are put in seperate buckets
def get_buckets_clashing_together(demands: list[int], overlapping_graph : nx.Graph, certain_overlap_graph :nx.Graph, max_buckets=5):

    buckets = [set() for i in range(min(len(demands),max_buckets))]
    visited_demands = set()
    demands_with_certain_overlap = [d for d in demands if len(list(certain_overlap_graph.neighbors(d))) > 0]

    buckets = __assign_buckets_based_on_graph(demands_with_certain_overlap, visited_demands, buckets, certain_overlap_graph, True)
    buckets = __assign_buckets_based_on_graph(demands, visited_demands,buckets, overlapping_graph, True)
    return buckets


#clique is a list containing a list of demands per clique
def get_buckets_clique(cliques: list[list[int]], max_buckets = 5):
    cliques.sort(key=lambda x: len(x), reverse=True)
    max_clique_size = max([len(clique) for clique in cliques])
    buckets = [[] for i in range(min(max_buckets, max_clique_size))]

    visited_demands = set()

    for clique in cliques:
        bucket_usage_for_clique = {b_id:0 for b_id in range(len(buckets))}

        for demand in clique:
            if demand in visited_demands:
                continue
            visited_demands.add(demand)

            # choose the buckets with least number of demands from the same clique. 
            candidate_buckets = [b_id for b_id,num_demands in bucket_usage_for_clique.items() if num_demands == min(bucket_usage_for_clique.values())]
            
            # for tiebreakers, choose from the smallest buckets
            smallest_size = min([len(buckets[b_id]) for b_id in candidate_buckets])
            candidate_buckets = [b_id for b_id in candidate_buckets if len(buckets[b_id]) == smallest_size]

            bucket_choice = random.choice(candidate_buckets)
            bucket_usage_for_clique[bucket_choice] += 1
            buckets[bucket_choice].append(demand)

    return buckets


if __name__ == "__main__":
    G = topology.get_nx_graph("topologies/topzoo/Mren.gml")
    demands = topology.get_gravity_demands_no_population(G,10, max_uniform=30, multiplier=1)
    #paths = topology.get_disjoint_simple_paths(G, demands, 2)  
    #cliques = topology.get_overlap_cliques(demands, paths)
    #overlaps,certain_overlap = topology.get_overlap_graph(demands, paths)

    #buckets = get_buckets_overlapping_graph(list(demands.keys()), overlaps, certain_overlap)
    buckets = get_buckets_bridge_node(demands,G)
    #print(cliques)
    print(buckets)