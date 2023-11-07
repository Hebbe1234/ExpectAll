#!/usr/bin/env python

import pulp
import pulp.apis
import networkx as nx
from networkx import digraph
from networkx import MultiDiGraph
from demands import Demand
from topology import get_demands
from topology import get_nx_graph
import argparse
import time
import os

os.environ["TMPDIR"] = "/scratch/fhyldg18"

def SolveUsingMIP(topology: MultiDiGraph, demands: list[Demand], wavelengths : int):
    
    def z_lookup(wavelenth : int):
        return "l"+str(wavelenth)

    def y_lookup(wavelenth : int, demand : int):
        return "l"+str(wavelenth)+"_"+"d"+str(demand)

    def x_lookup(wavelenth : int, edge : int, demand : int):
        return "l"+str(wavelenth)+"_e"+str(edge)+"_d"+str(demand)
    
    def match_edges(topology, e):
        for jj, ee in enumerate(topology.edges):
            if e[0] == ee[0] and e[1] == ee[1]:
                return jj
        
        assert("error")
        print("sdfsefsefsefse\n\n\n\n")
        exit()
        return -1

    
    start_time_all = time.perf_counter()

    z_var_dict = pulp.LpVariable.dicts('z',
                                       [ ("l"+str(i))for i in range(wavelengths)], lowBound=0, upBound=1, cat='Integer')
    y_var_dict = pulp.LpVariable.dicts('y',
                                       [("l"+str(wl) + "_" + "d"+str(d))
                                        for wl  in range(wavelengths)
                                        for d in range(len(demands))], lowBound=0, upBound=1, cat="Integer")
    x_var_dict = pulp.LpVariable.dicts('x',  
                                       [("l"+str(wl) + "_" + "e"+str(e) + "_"+"d" + str(d)) for wl  in range(wavelengths)
                                               for d in range(len(demands))
                                               for e, _ in enumerate(topology.edges)],
                                                 lowBound=0, upBound=1, cat="Integer")
 
    #8
    # Define the PuLP problem and set it to minimize
    prop = pulp.LpProblem('MyProblems:)', pulp.LpMinimize)
 
    # Define the objective function to minimize the sum of z_var_dict values
    objective = pulp.lpSum(z_var_dict.values())

    # Add the objective function to the problem
    prop += objective

    #10
    for d in range(len(demands)) :
        sum = 0
        for w in range(wavelengths):
            sum += y_var_dict[y_lookup(w,d)]
        prop += sum == 1

    #11
    for d in range(len(demands)):
        for e, _ in enumerate(topology.edges):
            for w in range(wavelengths):
                prop += x_var_dict[x_lookup(w,e,d)] <= z_var_dict[z_lookup(w)]

    #12
    for e, _ in enumerate(topology.edges):
        for w in range(wavelengths):
            sum = 0
            for d in range(len(demands)):
                sum += x_var_dict[x_lookup(w,e,d)]
            prop += sum <= 1
 
    #13
    for i, d in enumerate(demands):
        for w in range(wavelengths):
            y_sum = 0
            for j, e in enumerate(topology.in_edges(d.source)):
                kk = match_edges(topology,e)
                y_sum += x_var_dict[x_lookup(w,kk,i)]
            prop += y_sum == 0
            x_sum = 0
            #Makes infeasable
            for l, e in enumerate(topology.out_edges(d.source)):
                kk = match_edges(topology,e)
                x_sum += x_var_dict[x_lookup(w,kk,i)]
            prop += x_sum == y_var_dict[y_lookup(w,i)]
   
    #14
    for i, d in enumerate(demands):
        for w in range(wavelengths):
            y_sum = 0
            for j, e in enumerate(topology.out_edges(d.target)):
                kk = match_edges(topology,e)
                y_sum += x_var_dict[x_lookup(w,kk,i)]
            prop += y_sum == 0
            x_sum = 0
            for j, e in enumerate(topology.in_edges(d.target)):
                kk = match_edges(topology,e)
                x_sum += x_var_dict[x_lookup(w,kk,i)]
            prop += x_sum == y_var_dict[y_lookup(w,i)]
 

    #15
    for i, d in enumerate(demands):
        for w in range(wavelengths):
            for j, n in enumerate(topology.nodes):
                if n == d.source or n == d.target :
                    continue
 
                in_sum = 0
                for j, e in enumerate(topology.in_edges(n)):
                    kk = match_edges(topology,e)
                    in_sum += x_var_dict[x_lookup(w,kk,i)]
                out_sum = 0
                for j, e in enumerate(topology.out_edges(n)):
                    kk = match_edges(topology,e)
                    out_sum += x_var_dict[x_lookup(w,kk,i)]                
                prop += in_sum == out_sum
 
    start_time_solve = time.perf_counter()
    

    status = prop.solve(pulp.PULP_CBC_CMD(msg=False))
    end_time_all = time.perf_counter()  


    solved=True
    if pulp.constants.LpStatusInfeasible == status:
        print("Infeasable :(")
        solved = False

    solve_time = end_time_all - start_time_solve
    all_time = end_time_all - start_time_all

    print("solve time, all time, solvable")
    print(solve_time,",", all_time,",", solved)
    
    # Print the results
    # for var in prop.variables():
    #     print(f"{var.name} = {var.varValue}")


def SolveUsingMIP_SourceAggregation(topology: MultiDiGraph, demands: list[Demand], wavelengths : int):
    
    def x_lookup(wavelenth : int, edge : int, source : int):
        return "l"+str(wavelenth)+"_e"+str(edge)+"_s"+str(source)
    
    def p_lookup(source : int, destination: int):
        return "P_s" + str(source) + "_d" + str(destination)
    
    def destination_set(s):
        return [d.target for d in demands if d.source == s]
    
    def psd(s, d):
        return len([n for n in demands if n.source == s and n.target == d])
    
    def match_edges(topology, e):
        for jj, ee in enumerate(topology.edges):
            if e[0] == ee[0] and e[1] == ee[1]:
                return jj
        
        assert("error")
        print("sdfsefsefsefse\n\n\n\n")
        exit()
        return -1

    
    start_time_all = time.perf_counter()

    x_var_dict = pulp.LpVariable.dicts('x',  
                                       [("l"+str(w) + "_e"+str(e) + "_s" + str(s)) 
                                            for w  in range(wavelengths)
                                            for s in range(len(list(topology.nodes())))
                                            for e, _ in enumerate(topology.edges)],
                                        lowBound=0, upBound=1, cat="Integer")
    
    z_var_dict = pulp.LpVariable.dicts('z', [("w" + str(w)) for w  in range(wavelengths)], lowBound=0, upBound=1, cat="Integer")

    #8
    # Define the PuLP problem and set it to minimize
    prop = pulp.LpProblem('MyProblems:)', pulp.LpMinimize)
 
    # Define the objective function to minimize the sum of z_var_dict values
    
    obj_sum = 0
    for w in range(wavelengths):
        obj_sum += z_var_dict["w" + str(w)]
    
    objective = obj_sum

    # Add the objective function to the problem
    prop += objective
    #18
    for e, _ in enumerate(topology.edges):
        for w in range(wavelengths):
            x_sum = 0
            for i, s in enumerate(topology.nodes):
                x_sum += x_var_dict[x_lookup(w, e, i)]

            prop += x_sum <= 1
            
    #19
    for i, s in enumerate(topology.nodes):
        for w in range(wavelengths):
            x_sum = 0
            for e in topology.in_edges(s):
                kk = match_edges(topology, e)
                x_sum += x_var_dict[x_lookup(w, kk, i)]

            prop += x_sum == 0

    #20
    for i, s in enumerate(topology.nodes):
        for w in range(wavelengths):
            for j, d in enumerate(destination_set(s)):
                
                in_sum = 0
                for e_in in topology.in_edges(d):
                    kk = match_edges(topology, e_in)
                    in_sum += x_var_dict[x_lookup(w,kk,i)]
                out_sum = 0
                for e_out in topology.out_edges(d):
                    kk = match_edges(topology, e_out)
                    out_sum += x_var_dict[x_lookup(w,kk,i)]
                    
                prop += (in_sum >= out_sum)
 
    #21
    for i, s in enumerate(topology.nodes):
        for j, d in enumerate(destination_set(s)):
            
            in_sum = 0
            for w in range(wavelengths):
                for e_in in topology.in_edges(d):
                    kk = match_edges(topology, e_in)
                    in_sum += x_var_dict[x_lookup(w,kk,i)]
            
            out_sum = 0
            for w in range(wavelengths):
                for e_out in topology.out_edges(d):
                    kk = match_edges(topology, e_out)
                    out_sum += x_var_dict[x_lookup(w,kk,i)]
            
            prop += in_sum == (out_sum + psd(s,d))
   
    #22
    for i, s in enumerate(topology.nodes):
        for j, n in enumerate([n for n in topology.nodes() if (n != s) and n not in destination_set(s)]):
            for w in range(wavelengths):
                in_sum = 0
                for e_in in topology.in_edges(n):
                    kk = match_edges(topology, e_in)
                    in_sum += x_var_dict[x_lookup(w,kk,i)]

                out_sum = 0
                for e_out in topology.out_edges(n):
                    kk = match_edges(topology, e_out)
                    out_sum += x_var_dict[x_lookup(w,kk,i)]

                prop += in_sum == out_sum

    #23 - Basic Problem
    # for e, _ in enumerate(topology.edges):
    #     sum = 0
    #     for i, s in enumerate(topology.nodes):
    #         for w in range(wavelengths):
    #             sum += x_var_dict[x_lookup(w,e,i)]
            
    #     prop += sum <= z_max

    #24 - Extended problem Vs, Ve, Vw x_se^w <= <^w
    for i, s in enumerate(topology.nodes):
        for e, _ in enumerate(topology.edges):
            for w in range(wavelengths):
                prop += x_var_dict[x_lookup(w, e, i)] <= z_var_dict["w" + str(w)]

            
 
    start_time_solve = time.perf_counter()
    

    status = prop.solve(pulp.PULP_CBC_CMD(msg=False))
    end_time_all = time.perf_counter()  


    solved=True
    if pulp.constants.LpStatusInfeasible == status:
        print("Infeasable :(")
        solved = False

    solve_time = end_time_all - start_time_solve
    all_time = end_time_all - start_time_all

    print("solve time, all time, solvable")
    print(solve_time,",", all_time,",", solved)
    


def main():
    parser = argparse.ArgumentParser("mainmip.py")
    parser.add_argument("--filename", type=str, help="file to run on")
    parser.add_argument("--wavelengths", default=10, type=int, help="number of wavelengths")
    parser.add_argument("--demands", default=10, type=int, help="number of deamdns")
    parser.add_argument("--experiment", default="default", type=str, help="experiment to run")
    
    args = parser.parse_args()
    
    G = get_nx_graph("./topologies/topzoo/"+args.filename)
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    demands = get_demands(G, args.demands)
    demands = list(demands.values())
    print("hi")
    if args.experiment == "default":
        print("hello")
        SolveUsingMIP(G, demands, args.wavelengths)
    elif args.experiment == "source_aggregation":
        SolveUsingMIP_SourceAggregation(G, demands, args.wavelengths)
    
if __name__ == "__main__":
    main()

 

 
