import os
import pickle
from typing import Callable

from niceBDD import ChannelData
from niceBDDBlocks import EdgeFailoverNEvaluationBlock, UsageBlock

try:
    # raise ImportError()
    from dd.cudd import BDD as _BDD
    from dd.cudd import Function

    has_cudd = True
except ImportError:
   from dd.autoref import BDD as _BDD
   from dd.autoref import Function

   print("Using autoref... ")

def load_for_measurement(dir, id, measure: Callable):
    bdd_file = os.path.join(dir, "bdds",f"{id}.json")
    base_path = os.path.join(dir, "data",f"{id}_base.pickle") 
    expr_path = os.path.join(dir, "data",f"{id}_expr.pickle") 
    
    with open(base_path, "rb") as base_file:
        with open(expr_path, "rb") as expr_file:
            base = pickle.load(base_file)
            expr: Function = pickle.load(expr_file)
            bdd = _BDD()
            roots = bdd.load(bdd_file)
            print(f'Loaded BDD: {roots}')  
            base.bdd = bdd  
            
            print(base.demand_vars)
            # base.bdd.add_expr()
            
            print(measure(base, roots[0]))
                        
    result_file =os.path.join(dir, "results","11330885.json") 

class SolutionBlock():
    def __init__(self, expr):
        self.expr = expr

def usage(base, expr):
    cd: ChannelData = base.channel_data
    min_usage =min([len(c) for c in cd.unique_channels])
    max_slot=max([c[-1] for c in cd.unique_channels])

    for i in range(min_usage, max_slot+1):
        usage_block = UsageBlock(base,SolutionBlock(expr), i)
        if usage_block.expr != base.bdd.false:
            return i

def edge_evaluation(base, expr, k, dvs):
    k = EdgeFailoverNEvaluationBlock(base, SolutionBlock(expr),k, dvs)
    total_edges = 0
    solved_edges = 0
    for i,v in k.edge_to_failover.items(): 
        total_edges += 1
        if v: 
            solved_edges += 1
    return solved_edges, total_edges, (solved_edges * 100)/total_edges

load_for_measurement("../out/test", "test", lambda b,e: edge_evaluation(b,e, 2, False))