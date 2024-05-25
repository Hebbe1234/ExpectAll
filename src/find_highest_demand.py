import json
import os
import pandas as pd

def read_json_files(data_dirs):
    dfs = []
    for data_dir in data_dirs:
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                df = pd.read_json(os.path.join(data_dir, filename))
                dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

dir_path = "../out/EXPERIMENT_TOPOLOGY_ZOO_CLIQUE_RUN_8/results/"

df = read_json_files([dir_path])
df["topology"] = df["filename"].replace("\\", "/").str.replace(".gml", "").str.split("/").str[-1]

df = df[df["solved"] == True]
df = df.groupby(["topology"])["demands"].max().reset_index()

topology_to_max_demand = {}

for i,row in df.iterrows():
    topology_to_max_demand[row["topology"]] = row["demands"]
print(len(topology_to_max_demand.keys()))

with open("clique_true.json", "w") as f:
    json.dump(topology_to_max_demand,f)
