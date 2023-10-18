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

    zmax_var_dict = pulp.LpVariable.dicts('', 
                                       ["zmax"], lowBound=0, upBound=wavelengths, cat='Integer')
    zse_var_dict = {}

    for i,n in enumerate(topology.nodes):
        zse_dict    = {}
        t_s = 0
        for d in demands:
            if n == d.source:
                t_s +=1
        for e in topology.out_edges(n):
            zse_dict["z_s"+str(i)+"_e"+str(match_edges(topology,e))] = t_s #meh
        zse_var_dict.update( pulp.LpVariable.dicts('',
                                       [ (k) for k,v in zse_dict.items()], lowBound=0, upBound=t_s, cat="Integer"))
    
    print(zse_var_dict)    
    print(zmax_var_dict)

    # Define the PuLP problem and set it to minimize
    prob = pulp.LpProblem('MyProblems:)', pulp.LpMinimize)

    # Define the objective function to minimize the sum of z_var_dict values
    objective = pulp.lpSum(zmax_var_dict.values())

    # Add the objective function to the problem
    prob += objective


    #26
    for i,n in enumerate(topology.nodes):
        sum = 0
        for j,e in enumerate(topology.in_edges(n)):
            sum += zse_var_dict[zse_lookup(i, match_edges(topology,e))]
        prob += sum == 0
    
    print(prob)

    



    #zse_var_dict = pulp.LpVariable.dicts('zse', 
     #                                  [ ("s"+str(i)+"e"+str(k)) if e[0] == d.source for i,d in enumerate(demands) for k,e in enumerate(topology.edges) ], lowBound=0, upBound=1, cat='Integer')    

    exit()
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
    demands = [Demand("A","C"), Demand("A","C"), Demand("A","C")]
    #demands = list(demands.values())
    solve_routing(G, demands, 2)

if __name__ == "__main__":
    main()
