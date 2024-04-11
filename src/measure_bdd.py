import functools
import json
from multiprocessing import Pool
import os
import pickle
from typing import Callable

from niceBDD import ChannelData, FixedChannelsBDD, FixedChannelsDynamicVarsBDD, SubSpectrumBDD
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
    
    base_id = id
    if "_" in base_id:
        base_id = base_id.split("_")[0]

    base_path = os.path.join(data_dir,f"{base_id}_base.pickle") 
    bdd_file = os.path.join(bdd_dir,f"{id}.json")
    base_bdd_file = os.path.join(bdd_dir,f"{base_id}.json")
    result_file = os.path.join(results_dir,f"{base_id}.json")
    start_index_file = os.path.join(data_dir,f"{id}_start_index.json")
    
    
   
    
    with open(base_path, "rb") as base_file: 
        base_vars = []
        base = pickle.load(base_file)

        if id != base_id:
            all_base = base
            bdd = _BDD()
            roots = bdd.load(base_bdd_file)
            all_base.bdd = bdd  
            base_vars = list(all_base.bdd.vars.keys())

        
        bdd = _BDD()
        roots = bdd.load(bdd_file)
        if len(base_vars) > 0:
            bdd.declare(*base_vars)
            
        print(f'Loaded BDD: {roots}')  
        base.bdd = bdd  
        
        start_index = 0
        if os.path.exists(start_index_file):
            with open(start_index_file, "r") as jsonFile:
                start_index = int(json.load(jsonFile)["start_index"])
        
        res = {}
        with open(result_file, "r") as jsonFile:
            res = json.load(jsonFile)[0]
        
        with open(result_file, "r") as jsonFile:
            res = json.load(jsonFile)[0]
        
        if res.get(measure_key, None) is None:
            res[measure_key] = []
            
        print(base_id, id)
            
        res[measure_key].append(measure(base, roots[0], start_index))
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

def usage(base, expr, start_index = 0):
    cd: ChannelData = base.channel_data
    min_usage = min([len(c) for c in cd.unique_channels])
    max_slot= max([c[-1] for c in cd.unique_channels])
    
    if isinstance(base, FixedChannelsDynamicVarsBDD) or isinstance(base, FixedChannelsBDD):
        return base.usage
    
    for i in range(min_usage, max_slot+1):
        usage_block = UsageBlock(base,SolutionBlock(expr), i, start_index)
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

load_for_measurement("../out/EXPERIMENT_0_5_RUN_2", "usage", usage)