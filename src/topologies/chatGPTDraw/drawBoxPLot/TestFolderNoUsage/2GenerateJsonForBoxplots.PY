import os
import json

graphName = "dt"
name = graphName + "EdgeTop"
name = graphName + "Ands"
data_folder = '5k_FAILURES_ILP/'+name
data_folder = 'FAILOVER_MUCH_INFO/'+name

output_file = name+'.json'

outfolder = name
def extract():
    # Define the path to your Data folder
    # data_folder = 'EXPERIMENT_FAILOVER_MIP_RUN_3/kanto'

    # Initialize lists to store demands and all_times values
    demands_and_all_times = []

    # Iterate over each JSON file in the Data folder
    for filename in os.listdir(data_folder):
        if filename.endswith('.json'):
            file_path = os.path.join(data_folder, filename)
            
            # Open the JSON file and load its content
            with open(file_path, 'r') as f:
                data = json.load(f)
            data = data[0]
            # Extract demands and all_times values from the loaded data

            demands = data.get('demands')
            # all_times = data.get('all_times')
            all_times = data.get('time_points_2')
            
            # Append demands and all_times to the list
            demands_and_all_times.append({
                'demands': demands,
                'all_times': all_times
            })

    # Write the extracted data to a new JSON file
    with open(output_file, 'w') as f:
        json.dump(demands_and_all_times, f, indent=4)

def extractToMany():
    # Create a folder if it doesn't exist
    if not os.path.exists(outfolder):
        os.makedirs(outfolder)

    with open(output_file, 'r') as f:
        data = json.load(f)

    # Iterate through each set of all_times
    for i in range(5):
        new_data = []
        for item in data:
            new_item = {
                "demands": item["demands"],
                "all_times": [item["all_times"][i]]
            }
            new_data.append(new_item)
        
        # Write new data to a new JSON file in the json2 folder
        with open(outfolder+f'/EdgeFailover_{i+1}.json', 'w') as outfile:
            json.dump(new_data, outfile, indent=4)


import time
extract()
time.sleep(1)
extractToMany()
time.sleep(1)
