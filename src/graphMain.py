import topology
from bdd import RWAProblem, iben_print, BDD
from demands import Demand
import networkx as nx 
from itertools import permutations
from enum import Enum
import time
import draw
has_cudd = False

try:
    from dd.cudd import BDD as _BDD
    from dd.cudd import Function
    has_cudd = True
except ImportError:
   from dd.autoref import BDD as _BDD
   from dd.autoref import Function 
   print("Using autoref... ")

import networkx as nx
from networkx import digraph
from networkx import MultiDiGraph
import math
from demands import Demand
from itertools import permutations

class combineDemandsBlock():
    def __init__(self, solutions, ):
        
        self.expr = solutions[0].base.bdd.true
        for s in solutions:

            self.expr &= s.rwa
            
        print(self.expr.get_assignments())


if __name__ == "__main__":
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/simple_simple_net.dot"))
    G = topology.get_nx_graph(topology.TOPZOO_PATH +  "/Bren.gml")
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/simple_net.dot"))
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/split5NodeExample.dot"))

    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
    subgraphs, removedNode = topology.split_into_multiple_graphs(G)
    for g in subgraphs:
        print(g.nodes)
        print(g.edges)
        print("\n,")
    numOfDemands = 1
    demands = topology.get_demands(G, numOfDemands)
    demands = {0: Demand("A", "D"), 1: Demand("A", "E") }
    print("demands", demands)

    newDemandsDict , oldDemandsToNewDemands, graphToNewDemands = topology.split_demands(G, subgraphs, removedNode, demands)
    print(newDemandsDict)
    print(oldDemandsToNewDemands)
    print(graphToNewDemands)

    # types = [BDD.ET.EDGE, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH,BDD.ET.SOURCE]
    types = [BDD.ET.EDGE, BDD.ET.LAMBDA, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH,BDD.ET.SOURCE]
    # forced_order = [BDD.ET.LAMBDA, BDD.ET.EDGE, BDD.ET.NODE]
    # ordering = [t for t in types if t not in forced_order]
    # p = permutations(ordering)

    # Increasing wavelengths
    # for w in range(1,5+1):
    #     print(f"w: {w}")
    #     rw1 = RWAProblem(G, demands, forced_order+[*ordering], w, group_by_edge_order =True, generics_first=False)
    #     if rw1.rwa.count() > 0:
    #         print(rw1.get_assignments(1)[0])
    #         break  

    dict[int, Demand]
    solutions = []  
    wavelengths = 2
    print("Solve")
    for g in subgraphs: 

        if g in graphToNewDemands:
            demIndex = graphToNewDemands[g]
            res:dict[int,Demand] = {}
            for d in demIndex:
                res[d] = newDemandsDict[d]
            print(res)
            rw1 = RWAProblem(g, res, types, wavelengths=wavelengths, group_by_edge_order =True, generics_first=False, with_sequence=False, binary=True)
            solutions.append(rw1)
        else: 
            pass


    blockRes = combineDemandsBlock(solutions)


    # print(demands)
    # for i in range(1,10000): 
    #     assignments = blockRes.get_assignments(i)
       
    #     if len(assignments) < i:
    #         break
        
    #     draw_assignment(assignments[i-1], rw1.base, G)
    #     # time.sleep(0.01)
        
        
    





  #  print(rw1.base.bdd.to_expr(rw1.rwa))
    # print(rw1.rwa.count())
    
    # for i,o in enumerate(p):
    #     print(f"ordering being checked: {o}")
    #     # rwa = RWAProblem(G, demands, [*o], 5, group_by_edge_order =False, generics_first=False)
    #     # rwa = RWAProblem(G, demands, [*o], 5, group_by_edge_order =False, generics_first=True)
    #     rwa = RWAProblem(G, demands, forced_order+[*o], 5, group_by_edge_order =True, generics_first=False)
    #     rwa = RWAProblem(G, demands, forced_order+[*o], 5, group_by_edge_order =True, generics_first=True)
    #     # print(rwa.rwa.count())
    
    #rwa.print_assignments(true_only=True, keep_false_prefix="l")