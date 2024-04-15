import topology
from demands import Demand
import random
from numpy import array_split
import networkx as nx

# evenly splits demands into n buckets based on order
def get_buckets_naive(demands:dict[int,Demand], max_buckets=5):
    d_ids = list(demands.keys())
    return [list(a) for a in array_split(d_ids, min(max_buckets,len(d_ids)))]


# Split demands such that demands that overlap on any path are put in seperate buckets
def get_buckets_overlapping_graph(demands: list[int], overlapping_graph : nx.Graph, certain_overlap_graph :nx.Graph, max_buckets=5):
    def assign_buckets_based_on_graph(demands, visited_demands, buckets, overlapping_graph):
        #for each demand, choose the bucket that has the least number of overlaps on the demands that are already there
        for demand in demands:
            if demand in visited_demands:
                continue
            visited_demands.add(demand)

            current_overlaps_in_buckets = {i:0 for i in range(len(buckets))}

            #find number of overlaps with demands in each bucket
            for b_id,bucket in enumerate(buckets):
                neighbors = set(overlapping_graph.neighbors(demand))
                current_overlaps_in_buckets[b_id] = len([d for d in bucket if d in neighbors]) 
            
            choices = [b_id for b_id,overlap_count in current_overlaps_in_buckets.items() if overlap_count == min(current_overlaps_in_buckets.values())]
            
            #for tie breakers, choose smallest bucket
            smallest_bucket_size = min([len(buckets[b_id]) for b_id in choices])
            choice = [b_id for b_id in choices if len(buckets[b_id]) == smallest_bucket_size][0]

            buckets[choice].add(demand)

        return buckets

    buckets = [set() for i in range(min(len(demands),max_buckets))]
    visited_demands = set()
    demands_with_certain_overlap = [d for d in demands if len(list(certain_overlap_graph.neighbors(d))) > 0]

    buckets = assign_buckets_based_on_graph(demands_with_certain_overlap, visited_demands, buckets, certain_overlap_graph)
    buckets = assign_buckets_based_on_graph(demands, visited_demands,buckets, overlapping_graph)
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
    G = topology.get_nx_graph("topologies/japanese_topologies/kanto11.gml")
    demands = topology.get_gravity_demands(G,20, max_uniform=30, multiplier=1)
    paths = topology.get_disjoint_simple_paths(G, demands, 2)  
    cliques = topology.get_overlap_cliques(list(demands.values()), paths)
    overlaps,certain_overlap = topology.get_overlap_graph(list(demands.values()), paths)

    buckets = get_buckets_overlapping_graph(list(demands.keys()), overlaps, certain_overlap)

    #print(cliques)
    print(buckets)