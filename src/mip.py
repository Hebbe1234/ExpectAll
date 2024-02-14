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

os.environ["TMPDIR"] = "/scratch/rhebsg19/"

def SolveUsingMIP(topology: MultiDiGraph, demands: list[Demand], wavelengths : int):

    def z_lookup(wavelenth : int):
        return "l"+str(wavelenth)

    def y_lookup(wavelenth : int, demand : int):
        return "l"+str(wavelenth)+"_"+"d"+str(demand)

    def x_lookup(wavelenth : int, edge : int, demand : int):
        return "l"+str(wavelenth)+"_e"+str(edge)+"_d"+str(demand)

    def match_edges(topology, e):
        for jj, ee in enumerate(topology.edges(keys=True)):
            if e[0] == ee[0] and e[1] == ee[1] and e[2] == ee[2]:
                return jj

        assert("error")
        print("sdfsefsefsefse\n\n\n\n")
        exit()
        return -1


    start_time_constraint = time.perf_counter()


    z_var_dict = pulp.LpVariable.dicts('z',
                                       [ ("l"+str(i))for i in range(wavelengths)], lowBound=0, upBound=1, cat='Integer')
    y_var_dict = pulp.LpVariable.dicts('y',
                                       [("l"+str(wl) + "_" + "d"+str(d))
                                        for wl  in range(wavelengths)
                                        for d in range(len(demands))], lowBound=0, upBound=1, cat="Integer")
    x_var_dict = pulp.LpVariable.dicts('x',
                                       [("l"+str(wl) + "_" + "e"+str(e) + "_"+"d" + str(d)) for wl  in range(wavelengths)
                                               for d in range(len(demands))
                                               for e, _ in enumerate(topology.edges(keys=True))],
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
        for e, _ in enumerate(topology.edges(keys=True)):
            for w in range(wavelengths):
                prop += x_var_dict[x_lookup(w,e,d)] <= z_var_dict[z_lookup(w)]

    #12
    for e, _ in enumerate(topology.edges(keys=True)):
        for w in range(wavelengths):
            sum = 0
            for d in range(len(demands)):
                sum += x_var_dict[x_lookup(w,e,d)]
            prop += sum <= 1

    #13
    for i, d in enumerate(demands):
        for w in range(wavelengths):
            y_sum = 0
            for j, e in enumerate(topology.in_edges(d.source,keys=True)):
                kk = match_edges(topology,e)
                y_sum += x_var_dict[x_lookup(w,kk,i)]
            prop += y_sum == 0
            x_sum = 0
            #Makes infeasable
            for l, e in enumerate(topology.out_edges(d.source,keys=True)):
                kk = match_edges(topology,e)
                x_sum += x_var_dict[x_lookup(w,kk,i)]
            prop += x_sum == y_var_dict[y_lookup(w,i)]

    #14
    for i, d in enumerate(demands):
        for w in range(wavelengths):
            y_sum = 0
            for j, e in enumerate(topology.out_edges(d.target,keys=True)):
                kk = match_edges(topology,e)
                y_sum += x_var_dict[x_lookup(w,kk,i)]
            prop += y_sum == 0
            x_sum = 0
            for j, e in enumerate(topology.in_edges(d.target,keys=True)):
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
                for j, e in enumerate(topology.in_edges(n,keys=True)):
                    kk = match_edges(topology,e)
                    in_sum += x_var_dict[x_lookup(w,kk,i)]
                out_sum = 0
                for j, e in enumerate(topology.out_edges(n,keys=True)):
                    kk = match_edges(topology,e)
                    out_sum += x_var_dict[x_lookup(w,kk,i)]
                prop += in_sum == out_sum

    end_time_constraint = time.perf_counter()
    status = prop.solve(pulp.PULP_CBC_CMD(msg=False))

    solved=True
    if pulp.constants.LpStatusInfeasible == status:
        print("Infeasable :(")
        solved = False

    return start_time_constraint, end_time_constraint, solved
    # Print the results
    # for var in prop.variables():
    #     print(f"{var.name} = {var.varValue}")


def SolveUsingMIP_SourceAggregation(topology: MultiDiGraph, demands: list[Demand], wavelengths : int, print_optimal_wave=False):

    def x_lookup(wavelenth : int, edge : int, source : int):
        return "l"+str(wavelenth)+"_e"+str(edge)+"_s"+str(source)

    def p_lookup(source : int, destination: int):
        return "P_s" + str(source) + "_d" + str(destination)

    def destination_set(s):
        return [d.target for d in demands if d.source == s]

    def psd(s, d):
        return len([n for n in demands if n.source == s and n.target == d])

    def match_edges(topology, e):
        for jj, ee in enumerate(topology.edges(keys=True)):
            if e[0] == ee[0] and e[1] == ee[1] and e[2] == ee[2]:
                return jj

        assert("error")
        print("sdfsefsefsefse\n\n\n\n")
        exit()
        return -1


    start_time_constraint = time.perf_counter()

    x_var_dict = pulp.LpVariable.dicts('x',
                                       [("l"+str(w) + "_e"+str(e) + "_s" + str(s))
                                            for w  in range(wavelengths)
                                            for s in range(len(list(topology.nodes())))
                                            for e, _ in enumerate(topology.edges(keys=True))],
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
    for e, _ in enumerate(topology.edges(keys=True)):
        for w in range(wavelengths):
            x_sum = 0
            for i, s in enumerate(topology.nodes):
                x_sum += x_var_dict[x_lookup(w, e, i)]

            prop += x_sum <= 1

    #19
    for i, s in enumerate(topology.nodes):
        for w in range(wavelengths):
            x_sum = 0
            for e in topology.in_edges(s,keys=True):
                kk = match_edges(topology, e)
                x_sum += x_var_dict[x_lookup(w, kk, i)]

            prop += x_sum == 0

    #20
    for i, s in enumerate(topology.nodes):
        for w in range(wavelengths):
            for j, d in enumerate(destination_set(s)):

                in_sum = 0
                for e_in in topology.in_edges(d, keys=True):
                    kk = match_edges(topology, e_in)
                    in_sum += x_var_dict[x_lookup(w,kk,i)]
                out_sum = 0
                for e_out in topology.out_edges(d, keys=True):
                    kk = match_edges(topology, e_out)
                    out_sum += x_var_dict[x_lookup(w,kk,i)]

                prop += (in_sum >= out_sum)

    #21
    for i, s in enumerate(topology.nodes):
        for j, d in enumerate(destination_set(s)):

            in_sum = 0
            for w in range(wavelengths):
                for e_in in topology.in_edges(d,keys=True):
                    kk = match_edges(topology, e_in)
                    in_sum += x_var_dict[x_lookup(w,kk,i)]

            out_sum = 0
            for w in range(wavelengths):
                for e_out in topology.out_edges(d,keys=True):
                    kk = match_edges(topology, e_out)
                    out_sum += x_var_dict[x_lookup(w,kk,i)]

            prop += in_sum == (out_sum + psd(s,d))

    #22
    for i, s in enumerate(topology.nodes):
        for j, n in enumerate([n for n in topology.nodes() if (n != s) and n not in destination_set(s)]):
            for w in range(wavelengths):
                in_sum = 0
                for e_in in topology.in_edges(n,keys=True):
                    kk = match_edges(topology, e_in)
                    in_sum += x_var_dict[x_lookup(w,kk,i)]
                out_sum = 0
                for e_out in topology.out_edges(n,keys=True):
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
        for e, _ in enumerate(topology.edges(keys=True)):
            for w in range(wavelengths):
                prop += x_var_dict[x_lookup(w, e, i)] <= z_var_dict["w" + str(w)]



    end_time_constraint = time.perf_counter()

    status = prop.solve(pulp.PULP_CBC_CMD(msg=False))

    if print_optimal_wave:
        sum = 0
        for w in range(wavelengths):
            sum += pulp.value(z_var_dict["w" + str(w)])

        print(f"Optimal Wavelengths:{sum}")

    solved=True
    if pulp.constants.LpStatusInfeasible == status:
        print("Infeasable :(")
        solved = False

    return start_time_constraint, end_time_constraint, solved




def SolveUsingMIP_SourceAggregation_all(topology: MultiDiGraph, demands: list[Demand], wavelengths : int):

    def x_lookup(wavelenth : int, edge : int, source : int):
        return "l"+str(wavelenth)+"_e"+str(edge)+"_s"+str(source)

    def p_lookup(source : int, destination: int):
        return "P_s" + str(source) + "_d" + str(destination)

    def destination_set(s):
        return [d.target for d in demands if d.source == s]

    def psd(s, d):
        return len([n for n in demands if n.source == s and n.target == d])

    def match_edges(topology, e):
        for jj, ee in enumerate(topology.edges(keys=True)):
            if e[0] == ee[0] and e[1] == ee[1] and e[2] == ee[2]:
                return jj

        assert("error")
        print("sdfsefsefsefse\n\n\n\n")
        exit()
        return -1


    start_time_constraint = time.perf_counter()

    x_var_dict = pulp.LpVariable.dicts('x',
                                       [("l"+str(w) + "_e"+str(e) + "_s" + str(s))
                                            for w  in range(wavelengths)
                                            for s in range(len(list(topology.nodes())))
                                            for e, _ in enumerate(topology.edges(keys=True))],
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
    for e, _ in enumerate(topology.edges(keys=True)):
        for w in range(wavelengths):
            x_sum = 0
            for i, s in enumerate(topology.nodes):
                x_sum += x_var_dict[x_lookup(w, e, i)]

            prop += x_sum <= 1

    #19
    for i, s in enumerate(topology.nodes):
        for w in range(wavelengths):
            x_sum = 0
            for e in topology.in_edges(s, keys=True):
                kk = match_edges(topology, e)
                x_sum += x_var_dict[x_lookup(w, kk, i)]

            prop += x_sum == 0

    #20
    for i, s in enumerate(topology.nodes):
        for w in range(wavelengths):
            for j, d in enumerate(destination_set(s)):

                in_sum = 0
                for e_in in topology.in_edges(d,keys=True):
                    kk = match_edges(topology, e_in)
                    in_sum += x_var_dict[x_lookup(w,kk,i)]
                out_sum = 0
                for e_out in topology.out_edges(d,keys=True):
                    kk = match_edges(topology, e_out)
                    out_sum += x_var_dict[x_lookup(w,kk,i)]

                prop += (in_sum >= out_sum)

    #21
    for i, s in enumerate(topology.nodes):
        for j, d in enumerate(destination_set(s)):

            in_sum = 0
            for w in range(wavelengths):
                for e_in in topology.in_edges(d,keys=True):
                    kk = match_edges(topology, e_in)
                    in_sum += x_var_dict[x_lookup(w,kk,i)]

            out_sum = 0
            for w in range(wavelengths):
                for e_out in topology.out_edges(d,keys=True):
                    kk = match_edges(topology, e_out)
                    out_sum += x_var_dict[x_lookup(w,kk,i)]

            prop += in_sum == (out_sum + psd(s,d))

    #22
    for i, s in enumerate(topology.nodes):
        for j, n in enumerate([n for n in topology.nodes() if (n != s) and n not in destination_set(s)]):
            for w in range(wavelengths):
                in_sum = 0
                for e_in in topology.in_edges(n,keys=True):
                    kk = match_edges(topology, e_in)
                    in_sum += x_var_dict[x_lookup(w,kk,i)]

                out_sum = 0
                for e_out in topology.out_edges(n,keys=True):
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

    #24 - Extended problem Vs, Ve, Vw x_se^w <= z^w
    for i, s in enumerate(topology.nodes):
        for e, _ in enumerate(topology.edges(keys=True)):
            for w in range(wavelengths):
                prop += x_var_dict[x_lookup(w, e, i)] <= z_var_dict["w" + str(w)]

    end_time_constraint = time.perf_counter()
  
    i  = 0
        
    first = True
    done = False
    optimal_w = 0
    while done == False:
        print(i)
        status = prop.solve(pulp.PULP_CBC_CMD(msg=False))
        done = pulp.constants.LpStatusInfeasible == status

        if done:
            break

        if first:
            first = False
            for v in prop.variables():
                if "z" in v.name:
                    optimal_w += v.varValue

            print(optimal_w)


        cur_wavelengths = 0
        for v in prop.variables():
            if "z" in v.name:
                cur_wavelengths += v.varValue


        # print(cur_wavelengths)
        if cur_wavelengths > optimal_w:
            break

       
        bin_or_var = pulp.LpVariable(f"b_{i}", lowBound=0, upBound=1, cat="Integer")
        i += 1
        # print(type([v for v in prop.variables() if v.varValue == 1][0]))
        
        # for v in prop.variables():
        #     # print(v.varValue)
        #     print(f"{type(v)}, {type(v.varValue)}")
           
            
        # print("\n\n\n")
        # print({v.name: v.varValue for v in prop.variables() if not "b" in v.name})
        
        p1 = pulp.lpSum([v for v in prop.variables() if not "b" in v.name and v.varValue == 1])
        p2 = (pulp.lpSum([v for v in prop.variables() if not "b" in v.name and  v.varValue == 0])) + (len([v for v in prop.variables() if not "b" in v.name and v.varValue == 1]))

        M = 10000000
        c1 = p1 <= p2 - 1 + M * bin_or_var        
        c2 = p1 >= p2 + 1 - M * (1-bin_or_var)        
        
        # print(type(c1))
        # print(type(c2))
        
        # prop += (pulp.lpSum([v for v in prop.variables() if v.varValue == 1])) != (pulp.lpSum([v for v in prop.variables()]))
        prop += c1 
        prop += c2
        # prop += pulp.lpSum(z_var_dict["w" + str(1)]) >= 1
        
    return start_time_constraint, end_time_constraint, True

def Add_All(G, demands, wavelengths):
    solve_time = 0.0
    end_constraint_time = 0.0
    solved = True

    for i,d in enumerate(demands):
        start_constraint, end_constraint,problem_solved = SolveUsingMIP_SourceAggregation(G,demands[:i+1],wavelengths)

        solve_time += (time.perf_counter() - end_constraint)
        end_constraint_time += (end_constraint - start_constraint)
        solved = solved and problem_solved

    return solve_time, end_constraint_time, solved




def main():
    if not os.path.exists("/scratch/rhebsg19/"):
        os.makedirs("/scratch/rhebsg19/")

    parser = argparse.ArgumentParser("mainmip.py")
    parser.add_argument("--filename", type=str, help="file to run on")
    parser.add_argument("--wavelengths", default=2, type=int, help="number of wavelengths")
    parser.add_argument("--demands", default=1, type=int, help="number of demands")
    parser.add_argument("--experiment", default="default", type=str, help="default, source_aggregation, add_last, add_all")

    args = parser.parse_args()

    G = get_nx_graph(args.filename)
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    demands = get_demands(G, args.demands, 0, 10)
    demands = list(demands.values())
    print(demands)
    solved = False
    start_time_constraint = time.perf_counter()
    end_time_constraint = time.perf_counter()

    aggregated_time = False

    if args.experiment == "default":
        start_time_constraint, end_time_constraint, solved = SolveUsingMIP(G, demands, args.wavelengths)
    elif args.experiment == "source_aggregation":
        start_time_constraint, end_time_constraint, solved = SolveUsingMIP_SourceAggregation(G, demands, args.wavelengths)
    elif args.experiment == "source_aggregation_print":
        start_time_constraint, end_time_constraint, solved = SolveUsingMIP_SourceAggregation(G, demands, args.wavelengths, True)
    elif args.experiment == "source_aggregation_all":
        start_time_constraint, end_time_constraint, solved = SolveUsingMIP_SourceAggregation_all(G, demands, args.wavelengths)
    elif args.experiment == "add_last":
        start_time_constraint, end_time_constraint, solved = SolveUsingMIP_SourceAggregation(G, demands, args.wavelengths)
    elif args.experiment == "add_all":
        solve_time, constraint_time, solved = Add_All(G,demands,args.wavelengths)
        aggregated_time = True

    end_time_all = time.perf_counter()

    if not aggregated_time:
        solve_time = end_time_all - end_time_constraint
        constraint_time = end_time_constraint - start_time_constraint

    print("solve time;constraint time;all time;satisfiable;demands;wavelengths")
    print(f"{solve_time};{constraint_time};{solve_time + constraint_time};{solved};{args.demands};{args.wavelengths}")
    # print(f"{solve_time + constraint_time};{solve_time};{solved};{args.demands};{args.wavelengths}")




if __name__ == "__main__":
    main()




