#!/usr/bin/env python

import gurobipy as gp
from gurobipy import GRB
import networkx as nx
from networkx import MultiDiGraph
from demands import Demand
import topology
import argparse
import time
import os
import copy
from itertools import combinations
from channelGenerator import MipType

def run_mip_n(n:int, topology:nx.MultiDiGraph, demands, paths, slots):
    def get_combinations(nums, k):
        all_combinations = combinations(nums, k)
        unique_combinations = {tuple(sorted(comb)) for comb in all_combinations}
        return [list(comb) for comb in unique_combinations]
    
    edge_failure_combinations = get_combinations(topology.edges(keys=True),n)
    look_up = {}

    for combination in edge_failure_combinations:
        modified_graph = copy.deepcopy(topology)
        entry = tuple()
        legal_paths = copy.deepcopy(paths)

        for p in paths:
            for e in combination:
                if p in legal_paths and e in p:
                    legal_paths.remove(p)

        for e in combination:
            modified_graph.remove_edge(*e)
            entry += (e,)

        start_time_constraint, end_time_constraint, solved, optimale, demand_to_channels_res, demand_to_channels_res = SolveJapanMip(modified_graph, demands, legal_paths, slots,findAllSolutions=False)
        look_up[entry] = optimale

    return look_up

            

def SolveJapanMip(topology: MultiDiGraph, demands: dict[int,Demand], paths, slots: int, mipType = MipType.SINGLE, generated_solutions = -1):    

    def mip_parser(x_var_dict, demands: dict[int,Demand], demand_to_paths): 
        demand_to_used_channel = {i: [] for i,d in demands.items()}
        for id, d in demands.items():
            for p in demand_to_paths[id]:
                for s in range(0,slots): 
                    if x_var_dict[(id, p, s)].X == 1:
                        demand_to_used_channel[id].append([i for i in range(s,s+d.size)])

        return demand_to_used_channel

    def find_highest_used_slot(x_var_dict):
        highest_slot_used_so_far = -1
        for id, d in demands.items():
            for p in demand_to_paths[id]:
                for s in range(0,slots): 
                    if x_var_dict[(id, p, s)].X == 1:
                        used_slots = s + d.size - 1
                        highest_slot_used_so_far = max(used_slots, highest_slot_used_so_far)
        if highest_slot_used_so_far != -1:
            return highest_slot_used_so_far
        else : 
            print("errrrrrror")
            exit()

    def append_new_solution(x_var_dict, demands, demand_to_paths, demand_to_channels):
        res = mip_parser(x_var_dict, demands, demand_to_paths)
        for i,c in res.items():
            for channel in c:
                if channel not in demand_to_channels[i]:
                    demand_to_channels[i].append(channel)

        return demand_to_channels

    demand_to_paths = {i : [j for j,p in enumerate(paths) if p[0][0] == d.source and p[-1][1] == d.target] for i, d in demands.items()}

    
    def x_lookup(demand : int, path : int, slot : int):
        return "d" +str(demand)+"_p"+str(path)+"_s"+str(slot)
    

    env = gp.Env(empty=True)
    env.setParam('OutputFlag', 0)
    env.start()
    start_time_constraint = time.perf_counter()

    model = gp.Model('RSA:',env)

    # Variables
    x_var_dict = {(i, p, s): model.addVar(vtype=GRB.BINARY, name=x_lookup(i, p, s)) 
                  for i,d in demands.items()
                  for p in range(len(paths))
                  for s in range(0, slots)}
    w = model.addVar(lb=0, ub=slots, vtype=GRB.INTEGER, name="w")

    # Update model to integrate new variables
    model.update()
    
    # Set objective
    model.setObjective(w, GRB.MINIMIZE)

    # Constraints
    # Constraint 2
    for i,d in demands.items():
        _sum = 0
        for p in demand_to_paths[i]:
            _sum += gp.quicksum(x_var_dict[i, p, s] for s in range(slots - d.size + 1))
        model.addConstr(_sum == 1)

    # Constraint 3
    for s in range(slots): 
        for e in topology.edges: 
            _sum = 0
            for i,d in demands.items():
                for p in demand_to_paths[i]: 
                    if e not in paths[p]: 
                        continue
                    _sum += gp.quicksum(x_var_dict[i, p, ss] for ss in range(max(s-d.size+1,0), s+1))
            model.addConstr(_sum <= 1)

    # Constraint 5
    for i, d in demands.items():
        for p in demand_to_paths[i]:
            model.addConstr(gp.quicksum((s + d.size) * x_var_dict[i, p, s] for s in range(slots - d.size + 1)) <= w)

    # Solve model
    model.optimize()

    end_time_constraint = time.perf_counter()
    solved = False

    if model.status == GRB.Status.OPTIMAL:
        solved = True
        demand_to_channels_res = mip_parser(x_var_dict, demands, demand_to_paths)
    else:
        print("Infeasible :(")
        demand_to_channels_res = None
        return start_time_constraint, end_time_constraint, solved, -1, demand_to_channels_res, demand_to_channels_res


    optimale = find_highest_used_slot(x_var_dict)

    if mipType == MipType.SINGLE or not solved:
        return start_time_constraint, end_time_constraint, solved, optimale+1, demand_to_channels_res, demand_to_channels_res


    i  = 1
    optimal_slots = optimale
    print("gene", generated_solutions)
    demand_to_channels = demand_to_channels_res

    total_demand_sizes = len(demands)
    while True:

        if mipType in [MipType.EXHAUSTIVE, MipType.OLDOPTIMAL]:
            p1 = gp.quicksum([v for v in model.getVars() if v.X == 1])
            model.addConstr(p1 <= len([v for v in model.getVars() if v.X == 1]) - 1)

        elif mipType in [MipType.OLDSAFE, MipType.SAFE]:
            trueVariables =  [v.VarName for v in model.getVars() if v.X == 1]
            d_to_just_used_path = {}
            for d in demands.keys():
                var_for_d = [var for var in trueVariables if f"d{d}" in var][0] 
                start_index = var_for_d.find("p") + 1
                end_index = var_for_d.find("_s")
                path_index = int(var_for_d[start_index:end_index])
                
                d_to_just_used_path[d] = path_index
        
            _sum = 0
            for d,p in d_to_just_used_path.items():
                _sum += gp.quicksum(x_var_dict[(d,p,s)] for s in range(slots)) 
                
            k = _sum <= total_demand_sizes - 1
            model.addConstr(k)

        model.optimize()

        #MIP exhaustive and mip safe
        if model.status == GRB.Status.INFEASIBLE:
            break

        cur_slots = find_highest_used_slot(x_var_dict)
        
        #Mip optimal and Mip Safe
        if cur_slots > optimal_slots and mipType in [MipType.OLDOPTIMAL, MipType.OLDSAFE]:
            break
        
        demand_to_channels = append_new_solution(x_var_dict, demands, demand_to_paths, demand_to_channels)
        i += 1

        #only used by fixed channels, does not break the rest
        if i == generated_solutions:
            break

    return start_time_constraint, end_time_constraint, solved, optimale+1, demand_to_channels, demand_to_channels

def main():
    if not os.path.exists("/scratch/rhebsg19/"):
        os.makedirs("/scratch/rhebsg19/")
    os.environ["TMPDIR"] = "/scratch/rhebsg19/"
    

    parser = argparse.ArgumentParser("mainrsa_mip.py")
    parser.add_argument("--filename", default="./topologies/japanese_topologies/dt.gml", type=str, help="file to run on")
    parser.add_argument("--slots", default=320, type=int, help="number of slots")
    parser.add_argument("--demands", default=10, type=int, help="number of demands")
    parser.add_argument("--wavelengths", default=10, type=int, help="number of wavelengths")
    parser.add_argument("--experiment", default="default", type=str, help="default")
    parser.add_argument("--paths", default=2, type=int, help="how many paths")

    args = parser.parse_args()
    num_demands = args.demands
    num_slots = args.slots
    num_of_paths = args.paths

    G = topology.get_nx_graph(args.filename)
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    demands = topology.get_gravity_demands(G, num_demands, seed=10, offset=0, multiplier=1)
    paths = topology.get_disjoint_simple_paths(G, demands, num_of_paths)
    demand_channels = topology.get_channels(demands, num_slots, limit=False)
    demand_channels = topology.get_channels(demands, num_slots, limit=True)

    _, channels = topology.get_overlapping_channels(demand_channels)
    
    print(demands)
    solved = False
    start_time_constraint = time.perf_counter()
    end_time_constraint = time.perf_counter()



    if args.experiment == "default":
        start_time_constraint, end_time_constraint, solved, optimale, demand_to_channels_res, demand_to_channels_res = SolveJapanMip(G, demands, paths, num_slots, MipType.OLDSAFE)
    
    print("used slots:", optimale)
    print(demand_to_channels_res)

    end_time_all = time.perf_counter()

    solve_time = end_time_all - end_time_constraint
    constraint_time = end_time_constraint - start_time_constraint

    print("solve time;constraint time;all time;satisfiable;demands;slots")
    print(f"{solve_time};{constraint_time};{solve_time + constraint_time};{solved};{args.demands};{args.slots}")


if __name__ == "__main__":
    main()
