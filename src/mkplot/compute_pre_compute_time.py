
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

mip_query_amount = 10
heuristic_query_amount = 1000

def get_pre_compute_time(topology, experiment, solve_time, failures):
    num_edges = 36 if topology == "kanto11" else 52
    comb_amount = math.comb(num_edges, failures)
    query_amount = mip_query_amount if "mip" in experiment else heuristic_query_amount
    
    single_query_time = solve_time / query_amount
    
    time = single_query_time * comb_amount
    
    print(topology, experiment, solve_time, failures)
    print(single_query_time)
    
    

    
    print(time)
    return time

if __name__ == "__main__":
    data_dirs = ["../../out/MONDAY_MEETING/N_HEURISTIC/results", "../../out/MONDAY_MEETING/N_MIP/results"]
    out_dirs = ["../../out/MONDAY_MEETING/N_HEURISTIC_PRE_COMP/results/", "../../out/MONDAY_MEETING/N_MIP_PRE_COMP/results/"]
    
    for dd, od in zip(data_dirs, out_dirs):
        df = read_json_files([dd])
        df["topology"] = df["filename"].replace("\\", "/").str.replace(".gml", "").str.split("/").str[-1]

        
        df["build_time"] = df["solve_time"] 
        df["pre_compute_time"] = df.apply(lambda x: get_pre_compute_time(x.topology, x.experiment, x.solve_time, x.par1), axis=1)
        df["solve_time"] = df["pre_compute_time"]
        Path(od).mkdir(parents=True, exist_ok=True)

        df.to_json(od + "/with_pre_comp_time.json", orient='records')
        