import functools
import json
from multiprocessing import Pool
import os
import pickle
from typing import Callable

from niceBDD import ChannelData, FixedChannelsBDD, FixedChannelsDynamicVarsBDD
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

def measurement(filename, root, data_dir, bdd_dir, results_dir, measure_key, measure):
    # Print the full path of the file
    print(os.path.join(root, filename))
    id = filename.split(".")[0]

    base_path = os.path.join(data_dir,f"{id}_base.pickle") 
    bdd_file = os.path.join(bdd_dir,f"{id}.json")
    result_file = os.path.join(results_dir,f"{id}.json")
    
    with open(base_path, "rb") as base_file:
        base = pickle.load(base_file)
        bdd = _BDD()
        roots = bdd.load(bdd_file)
        print(f'Loaded BDD: {roots}')  
        base.bdd = bdd  
        
        res = {}
        with open(result_file, "r") as jsonFile:
            res = json.load(jsonFile)[0]

        res[measure_key] = measure(base, roots[0])
        print(id, res[measure_key])
        
        with open(result_file, "w") as jsonFile:
            json.dump([res], jsonFile, indent=4)
    
    
    
    
def load_for_measurement(dir, measure_key: str, measure: Callable):
    
    bdd_dir = os.path.join(dir, "bdds")
    data_dir =  os.path.join(dir, "data")
    results_dir = os.path.join(dir, "results")
 
    for root, dirs, files in os.walk(bdd_dir):
        for filename in files:
            measurement(filename, root=root, data_dir=data_dir, bdd_dir=bdd_dir, results_dir=results_dir, measure_key=measure_key, measure=measure)

class SolutionBlock():
    def __init__(self, expr):
        self.expr = expr

def usage(base, expr):
    cd: ChannelData = base.channel_data
    min_usage =min([len(c) for c in cd.unique_channels])
    max_slot=max([c[-1] for c in cd.unique_channels])
    
    if isinstance(base, FixedChannelsDynamicVarsBDD) or isinstance(base, FixedChannelsBDD):
        return base.usage
    
    for i in range(min_usage, max_slot+1):
        usage_block = UsageBlock(base,SolutionBlock(expr), i)
        if usage_block.expr != base.bdd.false:
            return i

def edge_evaluation(base, expr, k, is_dynamic_vars):
    k = EdgeFailoverNEvaluationBlock(base, SolutionBlock(expr),k, is_dynamic_vars)
    total_edges = 0
    solved_edges = 0
    for i,v in k.edge_to_failover.items(): 
        total_edges += 1
        if v: 
            solved_edges += 1
    return solved_edges, total_edges, (solved_edges * 100)/total_edges

load_for_measurement("../out/EXPERIMENT_0_7_RUN_2", "usage", usage)