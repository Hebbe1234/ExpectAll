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


def SolveUsingMIP(topology: MultiDiGraph, demands: list[Demand], wavelengths : int):
 

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


 

def main():
    parser = argparse.ArgumentParser("mainmip.py")
    parser.add_argument("--filename", type=str, help="file to run on")
    parser.add_argument("--wavelengths", default=10, type=int, help="number of wavelengths")
    parser.add_argument("--demands", default=10, type=int, help="number of deamdns")
    args = parser.parse_args()
    
    G = get_nx_graph("./topologies/topzoo/"+args.filename)
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    demands = get_demands(G, args.demands)
    demands = list(demands.values())
    SolveUsingMIP(G, demands, args.wavelengths)
    
if __name__ == "__main__":
    main()

 

 