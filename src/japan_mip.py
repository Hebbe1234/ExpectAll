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



def getLowerBound(topology: MultiDiGraph, demands: dict[int,Demand], paths, slots: int):
    def x_lookup(demand : int, path : int):
            return "d" +str(demand)+"_p"+str(path)
    
    demand_to_paths = {i : [j for j,p in enumerate(paths) if p[0][0] == d.source and p[-1][1] == d.target] for i, d in demands.items()}

    x_var_dict = pulp.LpVariable.dicts('x',
                                       ["d"+str(i)+"_p"+str(p)
                                        for i,_ in demands.items()
                                        for p in range(len(paths))], lowBound=0, upBound=1, cat="Integer")
    w = pulp.LpVariable.dicts('w',["ww"], lowBound=0, upBound=slots, cat="Integer")

    # Define the PuLP problem and set it to minimize 
    prob = pulp.LpProblem('RSA:)', pulp.LpMinimize)
    
    # Add the objective function to the problem
    prob += (w["ww"])        

    #constraint 1:
    for i in demands.keys():
        sum_ = 0
        for p in demand_to_paths[i]:
            sum_ += x_var_dict[x_lookup(i,p)]
        prob += sum_ == 1    

    #constraint 2:
    for e in topology.edges:
        sum_ = 0
        for i,d in demands.items():
            for p in demand_to_paths:
                if e not in paths[p]:
                    continue
                sum_ += x_var_dict[(x_lookup(i,p))] * d.size
        prob += sum_ <= w["ww"]
        
    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))

    varsdict = {v.name: v.varValue for v in prob.variables()}

    print("ww min :", varsdict["w_ww"])
    if pulp.constants.LpStatusInfeasible == status:
        print("Infeasable :(")
        return slots,{}
    
    #find path assignments:
    varsdict = {name: value for name, value in varsdict.items() if value >= 1}
    paths = {}
    for d in demands.keys():
        for p in demand_to_paths[d]:
                if f"x_{x_lookup(d,p)}" in varsdict.keys():
                    paths[d] = p
    
    return int(varsdict["w_ww"]), paths
        
def getUpperBound(topology: MultiDiGraph, demands: dict[int,Demand], demand_to_paths,paths, slots: int):
    def x_lookup(demand : int, slot : int):
            return "d" +str(demand)+"_s"+str(slot)
    
    #demand_to_paths = {i : [j for j,p in enumerate(paths) if p[0][0] == d.source and p[-1][1] == d.target] for i, d in demands.items()}

    x_var_dict = pulp.LpVariable.dicts('x',
                                       ["d"+str(i)+"_s"+str(s)
                                        for i,_ in demands.items()
                                        for s in range(slots)], lowBound=0, upBound=1, cat="Integer")
    w = pulp.LpVariable.dicts('w',["ww"], lowBound=0, upBound=slots, cat="Integer")

    # Define the PuLP problem and set it to minimize 
    prob = pulp.LpProblem('RSA:)', pulp.LpMinimize)
    
    # Add the objective function to the problem
    prob += (w["ww"])        

    #constraint 1:
    for i in demands.keys():
        sum_ = 0
        for s in range(slots):
            sum_ += x_var_dict[x_lookup(i,s)]
        prob += sum_ == 1    

    #constraint 2:
    for e in topology.edges:
        for s in range(slots):
            sum_ = 0
            for i,d in demands.items():
                    if e not in paths[demand_to_paths[i]]:
                        continue
                    for s_prime in range(max(s-d.size,0),s):
                        sum_ += x_var_dict[x_lookup(i,s_prime)]
            prob += sum_ <= 1

    #constraint 3:
    for i,d in demands.items():
        sum_ = 0
        for s in range(slots):
            sum_ += (s + d.size) * x_var_dict[(x_lookup(i,s))]
        prob += sum_ <= w["ww"]    

        
    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))

    varsdict = {v.name: v.varValue for v in prob.variables()}

    print("ww:", varsdict["w_ww"])

    if pulp.constants.LpStatusInfeasible == status:
        print("Infeasable :(")
        return slots
    
    return int(varsdict["w_ww"])    

def SolveJapanMip(topology: MultiDiGraph, demands: dict[int,Demand], paths, slots: int, findAllSolutions = False, generated_solutions = -1):    
    demand_to_paths = {i : [j for j,p in enumerate(paths) if p[0][0] == d.source and p[-1][1] == d.target] for i, d in demands.items()}

    def find_highest_used_slot(problem):
        highest_slot_used_so_far = -1
        for v in problem.variables():
            if v.varValue == 1: 
                start_index = v.name.find('d') + 1 # Find the index of 'd' and add 1 to start from the digit
                end_index = v.name.find('_p')  # Find the index of '_'
                demand_index = int(v.name[start_index:end_index])
                s_index = v.name.rfind('s')  # Find the index of the last occurrence of 's'
                number_after_s = int(v.name[s_index + 1:])
                highest_slot_used_by_demands = demands[demand_index].size + number_after_s - 1
                if highest_slot_used_by_demands > highest_slot_used_so_far: 
                    highest_slot_used_so_far = highest_slot_used_by_demands
        if highest_slot_used_so_far != -1:
            return highest_slot_used_so_far
        else : 
            print("errrrrrror")
            exit()

    def x_lookup(demand : int, path : int, slot : int):
        return "d" +str(demand)+"_p"+str(path)+"_s"+str(slot)
    
    start_time_constraint = time.perf_counter()

    x_var_dict = pulp.LpVariable.dicts('x',
                                       ["d"+str(i)+"_p"+str(p) + "_s"+str(s)
                                        for i,d in demands.items()
                                        for p  in range(len(paths))
                                        for s in range(0, slots)], lowBound=0, upBound=1, cat="Integer")
    w = pulp.LpVariable.dicts('w',["ww"], lowBound=0, upBound=slots, cat="Integer")

    # Define the PuLP problem and set it to minimize 
    prob = pulp.LpProblem('RSA:)', pulp.LpMinimize)
    
    # Add the objective function to the problem
    prob += (w["ww"])

    #Constraint 2:
    for i,d in demands.items():
        sum_ = 0
        for p in demand_to_paths[i]:
            for s in range(0,slots-d.size):
                sum_ += x_var_dict[x_lookup(i,p,s)]
        prob += sum_ == 1


    #Constraint 3
    for s in range(0,slots): 
        for e in topology.edges: 
            sum_ = 0
            for i,d in demands.items():
                for p in demand_to_paths[i]: 
                    if e not in paths[p] : 
                        continue
                    for ss in range(max(s-d.size,0), s): #Negative values?
                        sum_ += x_var_dict[x_lookup(i,p,ss)]
            prob += sum_ <= 1

    #constraint 5
    for i, d in demands.items():
        for p in demand_to_paths[i]:
            sum_ = 0
            for s in range(slots-d.size):
                sum_ += (s + d.size) * x_var_dict[x_lookup(i, p, s)]
            
            prob += sum_ <= w["ww"]

    def mip_parser(x_var_dict, demands: dict[int,Demand], demand_to_paths):
        demand_to_used_channel = {i: [] for i,d in demands.items()}
        for id, d in demands.items():
            for p in demand_to_paths[id]:
                for s in range(0,slots): 
                    if x_var_dict[x_lookup(id, p, s)].value() == 1:
                        demand_to_used_channel[id].append([i for i in range(s,s+d.size)])

        return demand_to_used_channel

    def append_new_solution(x_var_dict, demands, demand_to_paths, demand_to_channels):
        res = mip_parser(x_var_dict, demands, demand_to_paths)
        for i,c in res.items():
            for channel in c:
                if channel not in demand_to_channels[i]:
                    demand_to_channels[i].append(channel)

        return demand_to_channels


    end_time_constraint = time.perf_counter()
    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    varsdict = {}

    for v in prob.variables():
        varsdict[v.name] = v.varValue

    solved=True
    if pulp.constants.LpStatusInfeasible == status:
        print("Infeasable :(")
        optimal_number = slots
        solved = False
        return start_time_constraint, end_time_constraint, optimal_number, solved, None, None

    demand_to_channel = mip_parser(x_var_dict, demands, demand_to_paths)
    optimale = find_highest_used_slot(prob)


    if not findAllSolutions :
        return start_time_constraint, end_time_constraint, solved, optimale+1, demand_to_channel, None

    i  = 0
    first = True
    done = False
    optimal_slots = optimale
    print("optimal:", optimal_slots)
    print("gene", generated_solutions)
    if generated_solutions == -1:
        demand_to_channels = None
    else: 
        demand_to_channels = {i:[] for i,d in demands.items()}

    i  = 1
    optimal_slots = optimale
    print("gene", generated_solutions)
    demand_to_channels = demand_to_channel

    while True:

        p1 = pulp.lpSum([v for v in prob.variables() if v.varValue == 1])
        prob += p1 <= len([v for v in prob.variables() if v.varValue == 1]) - 1

        status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
        if pulp.constants.LpStatusInfeasible == status:
            break
        
        cur_slots = find_highest_used_slot(prob)
        if cur_slots > optimal_slots and generated_solutions == -1:
            break
        
        demand_to_channels = append_new_solution(x_var_dict, demands, demand_to_paths, demand_to_channels)
        i += 1
        
        if i == generated_solutions:
            break



    print(demand_to_channels)

    # while done == False or i < generated_solutions:
    #     status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    #     done = pulp.constants.LpStatusInfeasible == status


    #     if done:
    #         break

    #     if first:
    #         first = False
    #         optimal_slots = find_highest_used_slot(prob)

    #     cur_slots = find_highest_used_slot(prob)


    #     if cur_slots > optimal_slots:
    #         done = True

    #     #Used to generate channels for fixed channels!!!
    #     if i < generated_solutions: 
    #         done = True
    #         demand_to_channels = append_new_solution(x_var_dict, demands, demand_to_paths, demand_to_channels)

    #     p1 = pulp.lpSum([v for v in prob.variables() if v.varValue == 1])
    #     prob += p1 <= len([v for v in prob.variables() if v.varValue == 1]) - 1
    #     i += 1


    # print(demand_to_channels)
    return start_time_constraint, end_time_constraint, solved, optimale, demand_to_channel, demand_to_channels
    
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
    #paths = topology.get_simple_paths(G, demands, args.paths, shortest=False)
    paths = topology.get_disjoint_simple_paths(G, demands, 2)
    demand_channels = topology.get_channels(demands, num_slots, limit=False)
    demand_channels = topology.get_channels(demands, num_slots, limit=True)

    _, channels = topology.get_overlapping_channels(demand_channels)
    
    print(demands)
    solved = False
    start_time_constraint = time.perf_counter()
    end_time_constraint = time.perf_counter()

    
    if args.experiment == "default":
        start_time_constraint, end_time_constraint, solved, optimal, demand_to_channels_res, _ = SolveJapanMip(G, demands, paths, num_slots, False,-1)
    elif args.experiment == "lowerBound":
        getLowerBound(G,demands,paths,num_slots)
        exit()
    #print(demand_to_channels_res)
    print("optimal:", optimal)
    #This removes readlines below, since solveRSAUsingMip can return None. 
    if start_time_constraint is None or end_time_constraint is None or solved is None:
        exit()
    end_time_all = time.perf_counter()

    solve_time = end_time_all - end_time_constraint
    constraint_time = end_time_constraint - start_time_constraint

    print("solve time;constraint time;all time;satisfiable;demands;slots")
    print(f"{solve_time};{constraint_time};{solve_time + constraint_time};{solved};{args.demands};{args.slots}")
    # print(f"{solve_time + constraint_time};{solve_time};{solved};{args.demands};{args.wavelengths}")




if __name__ == "__main__":
    main()

