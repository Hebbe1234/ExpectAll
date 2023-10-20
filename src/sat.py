import pulp
import pulp.apis
import networkx as nx
from networkx import digraph
from networkx import MultiDiGraph
from demands import Demand
from topology import get_demands
import re
import copy
from pysat.solvers import Glucose3


def zse_lookup(node : int, edge : int):
    return "z_s"+str(node)+"_e"+str(edge)

def init_psd(demands : list[Demand]):
    psd = {}
    uniques = set(demands)
    for d in uniques:
        psd[d] = len([d2 for d2 in demands if d2 == d])

    return psd

def init_ds(topology: MultiDiGraph, demands : list[Demand]):
    ds_dict = {}
    for n in topology.nodes:
        ds = set()
        for d in demands:
            if d.source == n:
                ds.add(d.target)
        ds_dict[n] = list(ds)           

    return ds_dict


def solve_routing(topology: MultiDiGraph, demands: list[Demand], wavelengths : int):

    edge_index_lookup = {e:i for i,e in enumerate(topology.edges(data=False))}
    node_index_lookup = {n:i for i,n in enumerate(topology.nodes(data=False))}
    edge_lookup = {i:e for i,e in enumerate(topology.edges(data=False))}
    node_lookup = {i:n for i,n in enumerate(topology.nodes(data=False))}
    psd_dict : dict[Demand, int] = init_psd(demands)
    ds_dict  =  init_ds(topology, demands)

    zmax_var_dict = pulp.LpVariable.dicts('', 
                                       ["zmax"], lowBound=0, upBound=wavelengths, cat='Integer')
    zse_var_dict = {}
    for i,n in enumerate(topology.nodes):
        zse_vars  = set()
        ts = 0
        for d in demands:
            if n == d.source:
                ts += 1
        for e in topology.edges(data=False):
            zse_vars.add("z_s"+str(i)+"_e"+str(edge_index_lookup[e])) 
        zse_var_dict.update( pulp.LpVariable.dicts('',
                                       [z for z in zse_vars], lowBound=0, upBound=ts, cat='Integer' ))
    # Define the PuLP problem and set it to minimize
    prob = pulp.LpProblem('MyProblems:)', pulp.LpMinimize)

    # Define the objective function to minimize the sum of z_var_dict values
    objective = pulp.lpSum(zmax_var_dict.values())

    # Add the objective function to the problem
    prob += objective

    #26
    for i,n in enumerate(topology.nodes()):
        sum = 0
        for e in topology.in_edges(n):
            sum += zse_var_dict[zse_lookup(i, edge_index_lookup[e])]
        prob += sum == 0
    
    #27
    for i,s in enumerate(topology.nodes()):

        for d in ds_dict[s]:
            sum1 = 0
            sum2 = 0
            for e in topology.in_edges(d):
                sum1 += zse_var_dict[zse_lookup(i, edge_index_lookup[e])]
            for e in topology.out_edges(d):
                sum2 += zse_var_dict[zse_lookup(i, edge_index_lookup[e])]

            prob += (sum1 == (sum2 + psd_dict[Demand(s,d)])) 
                

    #28
    for i,s in enumerate(topology.nodes()):
        for j,n in enumerate(topology.nodes()):
            if n == s or n in ds_dict[s]:
                continue
            sum1 = 0
            sum2 = 0
            for e in topology.in_edges(n):
                sum1 += zse_var_dict[zse_lookup(i, edge_index_lookup[e])]
            for e in topology.out_edges(n):
                sum2 += zse_var_dict[zse_lookup(i, edge_index_lookup[e])]
            prob += sum1 == sum2

    #29
    for e in topology.edges():
        sum = 0
        for i,s in enumerate(topology.nodes()):
            sum += zse_var_dict[zse_lookup(i,edge_index_lookup[e])]
        prob += (sum <= zmax_var_dict["zmax"])


    status = prob.solve()
    if status == pulp.constants.LpStatusInfeasible:
        print("infeasable :(")

    res_dict = {}
    for var in prob.variables():
        print(var.name, var.varValue)
        node = re.search(r's(.*?)_', var.name)
        edge = re.search(r'_e(.*)', var.name)
        if edge and node:
            node_id = int(node.group(1))
            edge_id = int(edge.group(1))
            res_dict[node_lookup[node_id],edge_lookup[edge_id]] = var.varValue
        
    return res_dict, zmax_var_dict["zmax"].varValue
    

def find_path_fh(topology: MultiDiGraph, zse, node, path, demands, res, source, zse_prev):
    temp = copy.deepcopy(demands)
    for d in set(temp): # need to know how many demands are allowed to stop here. This depends on zse value of prev edge
        if d.target == node: 
            for i in range(int(zse_prev)): 
                res.append((d, path))
                demands.remove(d)
                
    for e in topology.out_edges(node):
        path_copy = copy.deepcopy(path)
        zse_prev = zse[(source, e)]

        if zse[(source, e)] > 0:
            zse[(source, e)] = zse[(source, e)] - 1

            path_copy.append(e)

            find_path_fh(topology, zse, e[1], path_copy, demands, res, source, zse_prev)

    return res

def alg_fh(topology, zse_dict, demands : list[Demand]):

    res_paths = []
    for node in topology.nodes:   
        demands_for_node = []
        for d in demands: 
            if d.source == node: 
                demands_for_node.append(d)

        res_paths.extend(find_path_fh(topology,zse_dict, node, [], demands_for_node, [], node, 0))

    return res_paths



def my_sat_solver(routes , wavelengths): 
 # Create a SAT solver instance
    with Glucose3() as g:

        demands = [] 
        for i,(d,list) in enumerate(routes): 
            demands.append(str(i)+str(d))

        Lambda = []  # Replace with your actual lambda elements
        for i in range(1,wavelengths):
            Lambda.append("L"+str(i))

        print(demands)
        print(Lambda)
        exit()
        # Generate CNF for Part 1 (53)
        generate_cnf_part_1(g, D, Lambda)
        
        # Generate CNF for Part 2 (54)
        generate_cnf_part_2(g, D, Lambda)
        
        # Generate CNF for Part 3 (55)
        generate_cnf_part_3(g, E, Lambda, D, p)
        
        # Check if the formula is satisfiable
        is_satisfiable = g.solve()
        
        if is_satisfiable:
            print("Satisfiable")
            # Get the satisfying assignment
            satisfying_assignment = g.get_model()
            print("Satisfying assignment:", satisfying_assignment)
        else:
            print("Unsatisfiable")

def generate_cnf_part_1(solver, D, Lambda):
    for d in D:
        for lambda1 in Lambda:
            for lambda2 in Lambda:
                if lambda1 != lambda2:
                    solver.add_clause([-var_num(lambda1, d), -var_num(lambda2, d)])

# def generate_cnf_part_2(solver, D, Lambda):
#     for d in D:
#         for lambda in Lambda:
#             solver.add_clause(var_num(lambda, d))

# def generate_cnf_part_3(solver, E, Lambda, D, p):
#     for e in E:
#         for lambda in Lambda:
#             d1_set = [d for d in D if p[d] == e]
#             for d1 in d1_set:
#                 for d2 in d1_set:
#                     if d1 != d2:
#                         solver.add_clause([-var_num(lambda, d1), -var_num(lambda, d2)])

def var_num(lambda_name, d):
    return 1  # You need to implement a mapping from variable names to variable numbers here





def main():
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/simple_net.dot"))
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    demands = [Demand("A","B"), Demand("A","B"),Demand("A","B"),Demand("A","B")]
    wavelengths = 2
    variables, z_max = solve_routing(G, demands, wavelengths)
    

    print(variables)
    all_routes = alg_fh(G, variables, demands)
    print("\n\n\n\n\n\n\n\n\n\n\n\n")
    my_sat_solver(all_routes, wavelengths)

if __name__ == "__main__":
    main()
