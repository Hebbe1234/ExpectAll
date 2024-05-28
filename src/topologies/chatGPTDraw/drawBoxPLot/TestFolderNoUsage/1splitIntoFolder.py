import os
import shutil
import json

# Define the source and destination directories
source_dir = "FAILOVER_MUCH_INFO_Old"
source_dir += '/results'
kanto_dynamic_dir = source_dir+'/kantoAnds'
kanto_failover_dir = source_dir+'/kantoEdgeTop'
dt_dynamic_dir = source_dir+'/dtAnds'
dt_failover_dir = source_dir+'/dtEdgeTop'

# Ensure destination directories exist
os.makedirs(kanto_dynamic_dir, exist_ok=True)
os.makedirs(kanto_failover_dir, exist_ok=True)
os.makedirs(dt_dynamic_dir, exist_ok=True)
os.makedirs(dt_failover_dir, exist_ok=True)

# Iterate through each file in the source directory
for filename in os.listdir(source_dir):
    if filename.endswith('.json'):
        filepath = os.path.join(source_dir, filename)

        # Read the content of the JSON file
        with open(filepath, 'r') as file:
            data = json.load(file)
            data = data[0]
            # Check the content of the file and copy it to the appropriate folder
            if 'kanto11' in data["filename"]:
                if 'failover_dynamic_query' in data["experiment"]:
                    shutil.copy(filepath, os.path.join(kanto_dynamic_dir, filename))
                elif 'failover_failover_query' in data["experiment"]:
                    shutil.copy(filepath, os.path.join(kanto_failover_dir, filename))
            elif 'dt' in data["filename"]:
                if 'failover_dynamic_query' in data["experiment"]:
                    shutil.copy(filepath, os.path.join(dt_dynamic_dir, filename))
                elif 'failover_failover_query' in data["experiment"]:
                    shutil.copy(filepath, os.path.join(dt_failover_dir, filename))

print("Files have been copied to the respective folders.")
