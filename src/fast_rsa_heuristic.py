import pulp
import pulp.apis
import networkx as nx
from networkx import digraph
from networkx import MultiDiGraph
from demands import Demand
import topology
import argparse
import time
import os

from topology import d_to_legal_path_dict
from demand_ordering import demand_order_sizes

# def find_used_channel(slot_start_index, demand : Demand, unique_channels):
#     for channel_id, channel in enumerate(unique_channels): 
#             if channel[0] == slot_start_index and len(channel) == demand.size: 
#                 return channel_id

def demand_to_original_index(original_demands_dics, demand):
    for i,d in original_demands_dics.items():
        if d == demand: 
            return i
    print("demand do not exist")
    exit()

def fastHeuristic(topology: MultiDiGraph, demands: dict[int,Demand], paths, slots: int):
    demand_to_used_channel = {d : [] for d in demands}
    demand_to_path = {}

    utilizedDict = {}
    for e in topology.edges(keys=True): 
        k = []
        for _ in range(slots):
            k.append(1)
        utilizedDict[e] = k
    d_to_its_k_paths = d_to_legal_path_dict(demands, paths)

    # reordered_demands = demand_order_sizes(demands, True)
    reordered_demands = demands
    for i, d in reordered_demands.items(): 
        options = []
        for path in d_to_its_k_paths[i]: 
            options.append(and_based_on_a_path(utilizedDict, paths[path]))
        best_slot_index = 23121231  #First is the index placement, the second is path index
        best_path_index = -1
        for ii, option in enumerate(options): 
            contiguesSlots = 0
            for slotIndex, s in enumerate(option): 
                if contiguesSlots == d.size: 
                    if best_slot_index > slotIndex-contiguesSlots : 
                        best_slot_index = slotIndex-contiguesSlots
                        best_path_index = ii
                    break
                if s == 1: 
                    contiguesSlots += 1
                else : 
                    contiguesSlots = 0

        if best_path_index == -1 : 
            print("Seems infeasiable")
            return None
        
        pathIndex = d_to_its_k_paths[i][best_path_index]

        demand_to_path[i] = best_path_index
        demand_to_used_channel[i].append([j for j in range(best_slot_index, best_slot_index + d.size)])
        
        path = paths[pathIndex]
        utilizedDict = update_vector_dict(utilizedDict, path, best_slot_index, d.size)
    print(demand_to_used_channel)
    return demand_to_used_channel



def update_vector_dict(edge_to_utlized, path, start_index, demand_size):
    for e in path: 
        current = edge_to_utlized[e]
        for s in range(start_index, start_index+demand_size):
            current[s] = 0
        edge_to_utlized[e] = current
    return edge_to_utlized





def and_based_on_a_path(edge_to_utlized, path):
    res_vector = []
    first = True 
    for e in path: 
        if first: 
            res_vector = edge_to_utlized[e]
            first = False
        else: 
            res_vector = [a and b for a,b in zip(edge_to_utlized[e], res_vector)]
    return res_vector





       
if __name__ == "__main__":
    G = topology.get_nx_graph("topologies/japanese_topologies/dt.gml")
    num_of_demands = 20
    num_of_slots = 45

    demands = topology.get_gravity_demands(G,num_of_demands, multiplier=1)
    print(demands)
    paths = topology.get_disjoint_simple_paths(G, demands, 2)
    start_time = time.perf_counter()
    demand_channels = topology.get_channels(demands, num_of_slots)

    demand_to_used_channels = fastHeuristic(G, demands, paths, num_of_slots)

    end_time = time.perf_counter()
    print(sum([d.size for d in demands.values()]))
    print(end_time-start_time)

  