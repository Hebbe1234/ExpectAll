import pulp
import pulp.apis
import networkx as nx
from networkx import digraph
from networkx import MultiDiGraph
from demands import Demand
from topology import get_demands

def zse_lookup(node : int, edge : int):
    return "z_s"+str(node)+"_e"+str(edge)


def match_edges(topology, e): 
    for jj, ee in enumerate(topology.edges): 
        if e[0] == ee[0] and e[1] == ee[1]: 
            return jj
    assert("error")
    print("sdfsefsefsefse\n\n\n\n")
    exit()
    return -1

def solve_routing(topology: MultiDiGraph, demands: list[Demand], wavelengths : int):

    edge_index_lookup = {e:i for i,e in enumerate(topology.edges(data=False))}
    node_index_lookup = {n:i for i,n in enumerate(topology.nodes(data=False))}

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
    for d in set(demands):
        sum = 0
        for e in topology.in_edges(d.source):
            sum += zse_var_dict[zse_lookup(node_index_lookup[d.source], edge_index_lookup[e])]
        prob += sum == 0
    
    
    print(prob)
    return



    #zse_var_dict = pulp.LpVariable.dicts('zse', 
     #                                  [ ("s"+str(i)+"e"+str(k)) if e[0] == d.source for i,d in enumerate(demands) for k,e in enumerate(topology.edges) ], lowBound=0, upBound=1, cat='Integer')    

 
    y_var_dict = pulp.LpVariable.dicts('y', 
                                       [("l"+str(wl) + "_" + "d"+str(d)) 
                                        for wl  in range(wavelengths) 
                                        for d in range(len(demands))], lowBound=0, upBound=1, cat="Integer")
    print(y_var_dict)
    x_var_dict = pulp.LpVariable.dicts('x',  
                                       [("l"+str(wl) + "_" + "e"+str(e) + "_"+"d" + str(d)) for wl  in range(wavelengths)
                                               for d in range(len(demands)) 
                                               for e, _ in enumerate(topology.edges)],
                                                 lowBound=0, upBound=1, cat="Integer")
    print(x_var_dict)

    #8
    # Define the PuLP problem and set it to minimize
    prop = pulp.LpProblem('MyProblems:)', pulp.LpMinimize)

    # Define the objective function to minimize the sum of z_var_dict values
    objective = pulp.lpSum(z_var_dict.values())

    # Add the objective function to the problem
    prop += objective
    
def main():
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/simple_net.dot"))
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
    #demands = get_demands(G, 10)
    demands = [Demand("C","B"), Demand("C","B")]

    #demands = list(demands.values())
    solve_routing(G, demands, 1)

if __name__ == "__main__":
    main()
