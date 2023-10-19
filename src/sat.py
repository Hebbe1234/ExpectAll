import pulp
import pulp.apis
import networkx as nx
from networkx import digraph
from networkx import MultiDiGraph
from demands import Demand
from topology import get_demands
import re

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
    print(zse_var_dict)
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
            print(s,n)
            print(sum1, " sum1")
            print(sum2, " sum2")
                
    #29
    for e in topology.edges():
        sum = 0
        for i,s in enumerate(topology.nodes()):
            sum += zse_var_dict[zse_lookup(i,edge_index_lookup[e])]
        prob += (sum <= zmax_var_dict["zmax"])


    print(prob)
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
    

def find_path(topology : MultiDiGraph, variables, current_node, current_path, demands : list[Demand], res_paths):
    
    #Test if we have found a node, which a demand wanted to reach and add it to our results. 
    if current_node is None: 
        print("AA")
        return res_paths
    new_demands_list = []
    for d in demands: 
        if d.target == current_node: 
            res_paths.append((d, current_path))
        else : 
            new_demands_list.append(d)

    for e in topology.out_edges(current_node):
        if variables[(current_node,e)] > 0:
            copy_current_path = current_path.deep
            print("dunkey", current_node, current_path)
            current_path.append(e)
            print(current_path)
            rrr = find_path(topology, variables, e[1], current_path, new_demands_list, res_paths)
            print(rrr)
            res_paths.extend(rrr)
    
    return res_paths

def myAlg(topology, variables: dict[str,int], demands : list[Demand]):

    res : dict[Demand, list[int]] = {}
    res_paths = []
    for i_node, node in enumerate(topology.nodes):   
        demands_for_node = []
        for d in demands: 
            if d.source == node: 
                demands_for_node.append(d)

        res_paths.extend(find_path(topology,variables, node, [], demands_for_node, []))
        return res_paths
    return res_paths


def main():
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/simple_net.dot"))
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
    #demands = get_demands(G, 10)
    demands = [Demand("A","B")]
    #demands = list(demands.values())
    variables, z_max = solve_routing(G, demands, 1)

    print(variables)
    print("\n\n\n\n\n\n\n\n\n\n\n\n")
    allRoutes = myAlg(G, variables, demands)
    print("hello", allRoutes)

if __name__ == "__main__":
    main()
