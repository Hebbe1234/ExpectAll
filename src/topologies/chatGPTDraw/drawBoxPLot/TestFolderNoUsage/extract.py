import os
import json

# Define the path to your Data folder
# data_folder = 'EXPERIMENT_FAILOVER_MIP_RUN_3/kanto'
data_folder = 'FAILOVER_MUCH_INFO/dtAnds'

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
        all_times = data.get('time_points')
        
        # Append demands and all_times to the list
        demands_and_all_times.append({
            'demands': demands,
            'all_times': all_times
        })

# Write the extracted data to a new JSON file
output_file = 'myData.json'
with open(output_file, 'w') as f:
    json.dump(demands_and_all_times, f, indent=4)

print(f"Data extracted and saved to '{output_file}'.")
