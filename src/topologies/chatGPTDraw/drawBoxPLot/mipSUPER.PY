import os
import json

graphName = "kanto"
name = graphName + "Mip"
data_folder = '5k_FAILURES_ILP/'+name

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
            all_times = data.get('all_times')
            
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

def fixValues():
        
    # Read the JSON file
    for i in range(1,5):
        fileTinh = outfolder+"/EdgeFailover_"+str(i)+".json"
        with open(fileTinh, 'r') as file:
            data = json.load(file)

        # Iterate over each object in the JSON data
        for obj in data:
            # Iterate over each list of values in the "all_times" attribute
            for times_list in obj['all_times']:
                prev_value = times_list[0]  # Get the first value as the previous value
                # Iterate starting from the second value
                for i in range(1, len(times_list)):
                    # Calculate the difference between the current value and the previous value
                    times_list[i] -= prev_value
                    prev_value += times_list[i]  # Update previous value for the next iteration

        # Write the modified data back to the JSON file
        with open(fileTinh, 'w') as file:
            json.dump(data, file, indent=4)



import time
extract()
time.sleep(1)
extractToMany()
time.sleep(1)
