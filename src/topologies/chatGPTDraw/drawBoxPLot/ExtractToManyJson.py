import os
import json

# Create a folder if it doesn't exist
if not os.path.exists('json2'):
    os.makedirs('json2')

with open('myData.json', 'r') as f:
    data = json.load(f)

# Iterate through each set of all_times
for i in range(3):
    new_data = []
    for item in data:
        new_item = {
            "demands": item["demands"],
            "all_times": [item["all_times"][i]]
        }
        new_data.append(new_item)
    
    # Write new data to a new JSON file in the json2 folder
    with open(f'json2/EdgeFailover_{i+1}.json', 'w') as outfile:
        json.dump(new_data, outfile, indent=4)
