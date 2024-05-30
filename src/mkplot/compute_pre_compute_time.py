
import json
import math
import os
from pathlib import Path
import pandas as pd

def read_json_files(data_dirs):
    dfs = []
    for data_dir in data_dirs:
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                df = pd.read_json(os.path.join(data_dir, filename))
                dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def get_pre_compute_time(topology, single_query_time, failures):
    num_edges = 36 if topology == "kanto11" else 52
    comb_amount = math.comb(num_edges, failures)
    
    time = single_query_time * comb_amount
 
    return time

def get_pre_compute_size(topology, demands, failures):
    num_edges = 36 if topology == "kanto11" else 52
    comb_amount = math.comb(num_edges, failures)
    
    return comb_amount * 2 * demands

if __name__ == "__main__":
    data_dirs = ["../../out/FINAL_MAYBE/EXPERIMENT_FAILOVER_MIP_FINAL_RUN_1/results"]
    out_dirs = ["../../out/FINAL_MAYBE/EXPERIMENT_FAILOVER_MIP_FINAL_RUN_1_PRECOMP/results/"]
    
    dns = []
    
    for dd, od in zip(data_dirs, out_dirs):
        Path(od).mkdir(parents=True, exist_ok=True)
        for fil in os.listdir(dd):
            with open(os.path.join(dd, fil), "r") as f:
                data_old = json.load(f)[0]
                data_new = [data_old for k in range(int(data_old["par1"]))]
                topology = data_old["filename"].replace("\\", "/").replace(".gml", "").split("/")[-1]

                all_times_old = data_old["all_times"]
                single_query_times = [sum(l)/len(l) for l in all_times_old]
        
                for i, dn in enumerate(data_new):
                    dn["par5"] = i+1
                    dn["all_times"]= []
                    dn["solve_time"] = get_pre_compute_time(topology, single_query_times[i], i+1)
                    dn["size"] = get_pre_compute_size(topology, dn["demands"], i+1)
                    dn["failover_plus_build_time"] = dn["solve_time"]
                    print(dn["solve_time"],dn["size"] )
                    dns.append(dn.copy())
        
        with open(os.path.join(od,  "pre_comps.json"), "w") as f:
            json.dump(dns, f, indent=4)