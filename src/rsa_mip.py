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

def SolveRSAUsingMIP(topology: MultiDiGraph, demands: dict[int,Demand], paths, channels, slots: int, findAllSolutions = False):    
    demand_to_paths = {i : [j for j,p in enumerate(paths) if p[0][0] == d.source and p[-1][1] == d.target] for i, d in demands.items()}
    demand_to_channels = {i : [j for j, c in enumerate(channels) if len(c) == d.size] for i, d in demands.items()}
    
    def y_lookup(demand : int, path : int, channel : int):
        return "d" +str(demand)+"_p"+str(path)+"_"+"c"+str(channel)

    def z_lookup(slot : int):
        return "s"+str(slot)

    def gamma(channel: int, slot: int):
        return slot in channels[channel]
    
    def delta(path: int, edge):
        return edge in paths[path]
       
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
    prob += (pulp.lpSum(z_var_dict[z_lookup(s)] for s in range(slots) ))

    #16
    for d in demands:
        sum_ = 0
        for p in demand_to_paths[d]:
            for c in demand_to_channels[d]:
                sum_ += y_var_dict[y_lookup(d, p,c)]
        prob += sum_ == 1

    #17
    for edge in topology.edges(keys=True):
        for s in range(slots):
            sum_ = 0
            for d in demands:
                for p in demand_to_paths[d]:
                    for c in demand_to_channels[d]:
                        sum_ += y_var_dict[y_lookup(d, p,c)] * gamma(c, s) * delta(p, edge)
            
            prob += sum_ <= 1

    #custom constraint
    for s in range(slots):
        sum_ = 0
        for d in demands:
            for p in demand_to_paths[d]:
                for c in demand_to_channels[d]:
                    prob += y_var_dict[y_lookup(d,p,c)] * gamma(c, s) <= z_var_dict[z_lookup(s)]

    end_time_constraint = time.perf_counter()
    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    optimal_number = int(sum(z_var_dict[z_lookup(s)].value() for s in range(slots) ))



    solved=True
    if pulp.constants.LpStatusInfeasible == status:
        print("Infeasable :(")
        optimal_number = slots
        solved = False
        return None, None, None, None, None
    
    def mip_parser(y_var_dict, demands, demand_to_paths, demand_to_channels):
        demand_to_used_channel = {}
        for d in demands:
            for p in demand_to_paths[d]:
                for c in demand_to_channels[d]:
                    if y_var_dict[y_lookup(d, p,c)].value() == 1:
                        demand_to_used_channel[d] = [channels[c]]
        return demand_to_used_channel
    
    #Now fixedChannels do not work
    #return mip_parser(y_var_dict, demands, demand_to_paths, demand_to_channels)


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
        print(p1)
        prob += p1 <= len([v for v in prob.variables() if "p" in v.name and v.varValue == 1]) - 1
        i += 1
        print(i)
        
    print(i)
    
    return start_time_constraint, end_time_constraint, solved, optimal_number, mip_parser(y_var_dict, demands, demand_to_paths, demand_to_channels)

def main():
    if not os.path.exists("/scratch/rhebsg19/"):
        os.makedirs("/scratch/rhebsg19/")

    parser = argparse.ArgumentParser("mainrsa_mip.py")
    parser.add_argument("--filename", default="./topologies/japanese_topologies/dt.gml", type=str, help="file to run on")
    parser.add_argument("--slots", default=320, type=int, help="number of slots")
    parser.add_argument("--demands", default=10, type=int, help="number of demands")
    parser.add_argument("--wavelengths", default=10, type=int, help="number of wavelengths")
    parser.add_argument("--experiment", default="default", type=str, help="default")
    parser.add_argument("--paths", default=2, type=int, help="how many paths")

    args = parser.parse_args()

    G = topology.get_nx_graph(args.filename)
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    demands = topology.get_gravity_demands(G, args.demands, seed=10, offset=0, multiplier=1)
    demands = topology.make_demands_size_n(demands, 1)
    #paths = topology.get_simple_paths(G, demands, args.paths, shortest=False)
    paths = topology.get_disjoint_simple_paths(G, demands, 1)
    demand_channels = topology.get_channels(demands, args.slots, limit=False)

    _, channels = topology.get_overlapping_channels(demand_channels)
    print(channels)
    
    print(demands)
    solved = False
    start_time_constraint = time.perf_counter()
    end_time_constraint = time.perf_counter()

    
    if args.experiment == "default":
        start_time_constraint, end_time_constraint, solved, optimal_number,_ = SolveRSAUsingMIP(G, demands, paths, channels, args.slots, True)
    #This removes readlines below, since solveRSAUsingMip can return None. 
    if start_time_constraint == None or end_time_constraint == None or solved == None or optimal_number == None:
        exit()

    end_time_all = time.perf_counter()

    solve_time = end_time_all - end_time_constraint
    constraint_time = end_time_constraint - start_time_constraint

    print("solve time;constraint time;all time;satisfiable;demands;slots")
    print(f"{solve_time};{constraint_time};{solve_time + constraint_time};{solved};{args.demands};{args.slots}")
    # print(f"{solve_time + constraint_time};{solve_time};{solved};{args.demands};{args.wavelengths}")




if __name__ == "__main__":
    main()

