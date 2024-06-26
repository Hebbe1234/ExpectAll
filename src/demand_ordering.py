import math
import networkx as nx
from demands import Demand
import random
import random

def demand_order_random(input_dict, seed=10):
    items = list(input_dict.items())
    random.seed(seed)
    random.shuffle(items)
    shuffled_dict = dict(items)
    
    return shuffled_dict


#Maybe get the other demand_order_sizes work, by changing the order. 
def demand_order_sizes_reorder_dict(input_dict):
    sorted_dict = dict(sorted(input_dict.items(), key=lambda x: getattr(x[1], "size"), reverse=True))

    return sorted_dict

def demand_order_sizes(demands: dict[int,Demand], largest_first=False):
    for i,d in demands.items():
        d.id = i
        
    demand_list = [demand for demand in demands.values()]
    demand_list = sorted(demand_list, key=lambda x: x.size, reverse=largest_first)
    demand_dict = {i:d for i,d in enumerate(demand_list)}

    demand_sizes = list(set([demand.size for demand in demand_list]))
    demand_sizes.sort(reverse=largest_first)

    new = {}
    for size in demand_sizes:
        temp = {i:d for i,d in demand_dict.items() if d.size == size}
        temp = demands_reorder_stepwise_similar_first(temp)
        new.update(temp)
    
    return new
      
def demands_reorder_stepwise_similar_first(demands):
    new_demands = {}
    visited_demmands = []

    for i,d in demands.items():
        for j,dd in demands.items():
            if i == j or (i in visited_demmands and j in visited_demmands):
                continue
            if d.source == dd.source and d.target == dd.target:
                new_demands.update({i:d,j:dd})
                visited_demmands.extend([i,j])
    

    for i,d in demands.items():
        for j,dd in demands.items():
            if i == j or (i in visited_demmands and j in visited_demmands):
                continue
            if d.source == dd.source:
                new_demands.update({i:d,j:dd})
                visited_demmands.extend([i,j])


    for i,d in demands.items():                 
        for j,dd in demands.items():
            if i == j or (i in visited_demmands and j in visited_demmands):
                continue
            if d.target == dd.target:
                new_demands.update({i:d,j:dd})
                visited_demmands.extend([i,j])

    #put in rest of demands
    for i,d in demands.items():                 
        if i not in visited_demmands:
            new_demands.update({i:d})
            visited_demmands.append(i)
    
    assert len(new_demands) == len(demands)

    return new_demands
                    

#A clique is a list of demand ids
def demand_order_cliques(demands: dict[int,Demand], cliques: list[list[int]], largest_first=False):
    demand_to_clique_size = {d:len(c) for did, d in demands.items() for c in cliques if did in c}
    clique_sizes = set(demand_to_clique_size.values()) #need to account for: different cliques can have same size


    demand_list = [demand for demand in demands.values()]
    demand_list = sorted(demand_list, key=lambda x: demand_to_clique_size[x], reverse=largest_first)

    demand_dict = {i:d for i,d in enumerate(demand_list)}
    new_dict = {}

    for size in clique_sizes:
        temp = {i:d for i,d in demand_dict.items() if demand_to_clique_size[d] == size}
        temp = demand_order_sizes(temp)
        ordered = {i:d for j,d in temp.items() for i,dd in demand_dict.items() if d == dd}
        new_dict.update(ordered)

    return new_dict

def get_demand_set(demands, node, isSource=True):
    if isSource:
        return [demand_id for demand_id, demand in demands.items() if demand.source == node]
    
    return [demand_id for demand_id, demand in demands.items() if demand.target == node]

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


def pretty_print_demands(demands):
    print(str(demands).replace(",","\n").replace("{"," ").replace("}",""))
        
def compare_demands_print(demands1, demands2, with_id=False):
    for d1,d2 in zip(demands1.items(), demands2.items()):
        if with_id:
            print(f"{d1} vs {d2}")
        else:
            print(f"{d1[1]} vs {d2[1]}")
        

if __name__ == "__main__":
	pass