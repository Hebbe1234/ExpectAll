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


def SolveJapanMip(topology: MultiDiGraph, demands: dict[int,Demand], paths, slots: int):    
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
        for p in demand_to_paths[i]:
            model.addConstr(gp.quicksum(x_var_dict[i, p, s] for s in range(slots - d.size + 1)) == 1)

    # Constraint 3
    for s in range(slots): 
        for e in topology.edges: 
            for i,d in demands.items():
                for p in demand_to_paths[i]: 
                    if e not in paths[p]: 
                        continue
                    model.addConstr(gp.quicksum(x_var_dict[i, p, ss] for ss in range(max(s-d.size+1,0), s+1)) <= 1)

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
        demand_to_channels_res = mip_parser(model, x_var_dict, demands, demand_to_paths)
    else:
        print("Infeasible :(")
        demand_to_channels_res = None

    return start_time_constraint, end_time_constraint, solved, None#demand_to_channels_res


def mip_parser(model, x_var_dict, demands: dict[int,Demand], demand_to_paths):
        
    def x_lookup(demand : int, path : int, slot : int):
        return "d" +str(demand)+"_p"+str(path)+"_s"+str(slot)
    
    demand_to_used_channel = {i: [] for i,d in demands.items()}
    for id, d in demands.items():
        for p in demand_to_paths[id]:
            for v in x_var_dict:
                print.VarName
                exit()
            #for s in range(model.getAttr(GRB.Attr.Start, x_var_dict[id, p, 0]),
            #               model.getAttr(GRB.Attr.Start, x_var_dict[id, p, model.NumVars])):
            #    if model.getVal(x_var_dict[id, p, s]) == 1:
            #        demand_to_used_channel[id].append(list(range(s, s + d.size)))

    return demand_to_used_channel


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
        start_time_constraint, end_time_constraint, solved, demand_to_channels_res = SolveJapanMip(G, demands, paths, num_slots)
    print(demand_to_channels_res)

    end_time_all = time.perf_counter()

    solve_time = end_time_all - end_time_constraint
    constraint_time = end_time_constraint - start_time_constraint

    print("solve time;constraint time;all time;satisfiable;demands;slots")
    print(f"{solve_time};{constraint_time};{solve_time + constraint_time};{solved};{args.demands};{args.slots}")


if __name__ == "__main__":
    main()
