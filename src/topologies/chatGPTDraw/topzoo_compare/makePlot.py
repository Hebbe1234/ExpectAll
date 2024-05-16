import os
import json
import matplotlib.pyplot as plt

# Define the path to your Data folder
data_folder = '../../../../out/EXPERIMENT_TOPOLOGY_ZOO_RUN_2/results'

# Initialize lists to store demands and all_times values
method_to_usage_and_topology = {}
topology_to_id = {}

# Iterate over each JSON file in the Data folder
for filename in os.listdir(data_folder):
    if filename.endswith('.json'):
        file_path = os.path.join(data_folder, filename)
        
        # Open the JSON file and load its content
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        data = data[0]
        experiment = data["experiment"]
        topology = data["filename"]
        usage = data["usage"]

        if experiment not in method_to_usage_and_topology.keys():
            method_to_usage_and_topology[experiment] = []
        
        if topology not in topology_to_id.keys():
            id = len(topology_to_id.keys())
            topology_to_id[topology] = id
            method_to_usage_and_topology[id] = {}
        
        id = topology_to_id[topology]

        method_to_usage_and_topology[id][experiment] = usage
    
    #print(method_to_usage_and_topology)

ratio_data = {"x":[], "y":[]}

for topology, exp_to_usage in method_to_usage_and_topology.items():
    exp_to_usage = dict(exp_to_usage)
    experiments = exp_to_usage.keys()
    experiments = sorted(experiments)
    
    if len(experiments) == 2:
        y = exp_to_usage[experiments[0]] / exp_to_usage[experiments[1]]

        ratio_data["x"].append(topology)
        ratio_data["y"].append(y)

x = ratio_data["x"]
y = ratio_data["y"]
plt.plot(x,y)
# Adding labels
plt.xlabel('instance')
plt.ylabel('ratio')
plt.title('Ratio plot of BDD usage and ILP usage')

# Setting x-axis ticks
#plt.xticks(range(1, len(data) + 1), [item['demands'] for item in data])

# Setting y-axis lower limit to 0
#plt.ylim(bottom=0)
plt.savefig("ratio")
#print(ratio_data)
    

        
