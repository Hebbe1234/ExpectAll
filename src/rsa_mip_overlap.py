#!/usr/bin/env python

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

os.environ["TMPDIR"] = "/scratch/rhebsg19/"

def getDemandPairsToChannelOverlaps(demands, channels, demand_to_channels):
    demand_pairs_to_channel_overlaps = {(demand1,demand2): [] for demand1 in demands for demand2 in demands}
    
    for demand1 in demands:
        for demand2 in demands:
            for channel1 in demand_to_channels[demand1]:
                for channel2 in demand_to_channels[demand2]:
                    if channels[channel1][0] >= channels[channel2][0] and channels[channel1][0] <= channels[channel2][-1] \
                    or channels[channel2][0] >= channels[channel1][0] and channels[channel2][0] <= channels[channel1][-1]:
                        demand_pairs_to_channel_overlaps[(demand1, demand2)].append((channel1, channel2))
    
    return demand_pairs_to_channel_overlaps

def getDemandPairsToPathOverlaps(demands, paths, overlapping_paths, demand_to_paths):
    demand_pairs_to_path_overlaps = {(demand1,demand2): [] for demand1 in demands for demand2 in demands}
    
    for demand1 in demands:
        for demand2 in demands:
            for path1 in demand_to_paths[demand1]:
                for path2 in demand_to_paths[demand2]:
                    if (path1, path2) in overlapping_paths:
                        demand_pairs_to_path_overlaps[(demand1, demand2)].append((path1, path2))
    
    return demand_pairs_to_path_overlaps
                        

def SolveRSAUsingMIPWithOverlaps(topology: MultiDiGraph, demands: dict[int,Demand], paths, channels, slots: int, overlapping_paths, findAllSolutions = False):    
    demand_to_paths = {i : [j for j,p in enumerate(paths) if p[0][0] == d.source and p[-1][1] == d.target] for i, d in demands.items()}
    demand_to_channels = {i : [j for j, c in enumerate(channels) if len(c) == d.size] for i, d in demands.items()}
    
    demand_pairs_to_channel_overlaps = getDemandPairsToChannelOverlaps(demands, channels, demand_to_channels)
    demand_pairs_to_path_overlaps = getDemandPairsToPathOverlaps(demands, paths, overlapping_paths, demand_to_paths)

    def y_lookup(demand : int, path : int, channel : int):
        return "d" +str(demand)+"_p"+str(path)+"_"+"c"+str(channel)

    def z_lookup(slot : int):
        return "s"+str(slot)

    def gamma(channel: int, slot: int):
        return slot in channels[channel]
    
    def delta(path: int, edge):
        return edge in paths[path]
    
    def overlapPath(demand1: int, demand2: int, path1: int, path2: int):
        return (path1, path2) in demand_pairs_to_path_overlaps[(demand1, demand2)]
    
    def overlapChannel(demand1: int, demand2: int, channel1: int, channel2: int):
        return (channel1, channel2) in demand_pairs_to_path_overlaps[(demand1, demand2)]
       
    start_time_constraint = time.perf_counter()

    y_var_dict = pulp.LpVariable.dicts('y',
                                       [("d"+str(d)+"_p"+str(p) + "_" + "c"+str(c))
                                        for d in demands
                                        for p  in range(len(paths))
                                        for c in range(len(channels))], lowBound=0, upBound=1, cat="Integer")
    
    z_var_dict = pulp.LpVariable.dicts('z',
                                       [("s"+str(s))
                                        for s in range(slots)], lowBound=0, upBound=1, cat="Integer")
    
    # Define the PuLP problem and set it to minimize 
    prob = pulp.LpProblem('RSA:)', pulp.LpMinimize)
    
    # prob += (pulp.lpSum(gamma(c,s) * y_var_dict[y_lookup(d, p, c)] for s in range(slots)
    #                                       for d in demands
    #                                       for p in demand_to_paths[d]
    #                                       for c in demand_to_channels[d]))
    # Define the objective function to minimize the sum of z_var_dict values
  
    # Add the objective function to the problem
    prob += (pulp.lpSum(z_var_dict[z_lookup(s)] for s in range(slots)))
    
    #16
    for d in demands:
        sum_ = 0
        for p in demand_to_paths[d]:
            for c in demand_to_channels[d]:
                sum_ += y_var_dict[y_lookup(d, p,c)]
        prob += sum_ == 1

    start = time.perf_counter()
    print("Starting... ")
    # for edge in topology.edges(keys=True):
    #     for s in range(slots):
    #         sum_ = 0
    #         for d in demands:
    #             for p in demand_to_paths[d]:
    #                 for c in demand_to_channels[d]:
    #                     sum_ += y_var_dict[y_lookup(d, p,c)] * gamma(c, s) * delta(p, edge)
            
    #         prob += sum_ <= 1
    # New
    for demand1 in demands:
        for demand2 in demands:
            if demand1 <= demand2:
                continue
            sum_ = 0
            #reached_inner_loop = False
            
            for (path1, path2) in demand_pairs_to_path_overlaps[(demand1, demand2)]:
                for (channel1, channel2) in demand_pairs_to_channel_overlaps[(demand1, demand2)]:
                    #reached_inner_loop = True
                    prob += 2 - y_var_dict[y_lookup(demand1, path1, channel1)] - y_var_dict[y_lookup(demand2, path2,channel2)] >= 1
            
            # if reached_inner_loop:
            #     prob += sum_ >= 1
    
    print("Overlapping constraints added in: ", (time.perf_counter() - start)*1000, " ms")
                
    #custom constraint
    for s in range(slots):
        sum_ = 0
        for d in demands:
            for p in demand_to_paths[d]:
                for c in demand_to_channels[d]:
                    prob += y_var_dict[y_lookup(d,p,c)] * gamma(c, s) <= z_var_dict[z_lookup(s)]

    print("Finished hahahaah")
    
    end_time_constraint = time.perf_counter()
    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    optimal_number = int(sum(z_var_dict[z_lookup(s)].value() for s in range(slots) ))


    solved=True
    if pulp.constants.LpStatusInfeasible == status:
        print("Infeasable :(")
        optimal_number = slots
        solved = False
        return start_time_constraint, end_time_constraint, solved, optimal_number, None
    
    def mip_parser(y_var_dict, demands, demand_to_paths, demand_to_channels):
        demand_to_used_channel = {}
        for d in demands:
            for p in demand_to_paths[d]:
                for c in demand_to_channels[d]:
                    if y_var_dict[y_lookup(d, p,c)].value() == 1:
                        demand_to_used_channel[d] = [channels[c]]
        return demand_to_used_channel
    

    if not findAllSolutions :
        return start_time_constraint, end_time_constraint, solved, optimal_number, mip_parser(y_var_dict, demands, demand_to_paths, demand_to_channels)

    i  = 0
    first = True
    done = False
    optimal_slots = 0
    while done == False:
        status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
        done = pulp.constants.LpStatusInfeasible == status

        if done:
            break

        if first:
            first = False
            for v in prob.variables():
                if "z" in v.name:
                    optimal_slots += v.varValue

            print(optimal_slots)


        cur_slots = 0
        for v in prob.variables():
            if "z" in v.name:
                cur_slots += v.varValue


        # print(cur_wavelengths)
        if cur_slots > optimal_slots:
            break

        p1 = pulp.lpSum([v for v in prob.variables() if "p" in v.name and v.varValue == 1])
        prob += p1 <= len([v for v in prob.variables() if "p" in v.name and v.varValue == 1]) - 1
        i += 1
        
    print(i)
    
    return start_time_constraint, end_time_constraint, solved, optimal_number, mip_parser(y_var_dict, demands, demand_to_paths, demand_to_channels)

def main():
    G = topology.get_nx_graph("topologies/japanese_topologies/kanto11.gml")
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    k_paths = 2
    number_of_demands = 10
    slots = 50
    
    demands = topology.get_gravity_demands(G, number_of_demands, seed=10, offset=0, multiplier=1)
    paths = topology.get_disjoint_simple_paths(G, demands, k_paths)
    demand_channels = topology.get_channels(demands, slots, limit=True)

    _, channels = topology.get_overlapping_channels(demand_channels)
    overlapping_paths = topology.get_overlapping_simple_paths(paths)
    
    print(demands)
    
    solved = False
    start_time_constraint = time.perf_counter()
    end_time_constraint = time.perf_counter()

    
    start_time_constraint, end_time_constraint, solved, optimal_number,mip_parsed = SolveRSAUsingMIPWithOverlaps(G, demands, paths, channels, slots, overlapping_paths, False)
    print(mip_parsed)
    print(optimal_number)
    end_time_all = time.perf_counter()

    solve_time = end_time_all - end_time_constraint
    constraint_time = end_time_constraint - start_time_constraint

    print("solve time;constraint time;all time;satisfiable;demands;slots")
    print(f"{solve_time};{constraint_time};{solve_time + constraint_time};{solved};{number_of_demands};{slots}")
    # print(f"{solve_time + constraint_time};{solve_time};{solved};{args.demands};{args.wavelengths}")




if __name__ == "__main__":
    main()
    