import os
import json

def process_json_file(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    for item in data:
        time_points = item['time_points']
        usage_times = item['usage_times']
        
        # Subtract usage_times from time_points elementwise
        time_points_2 = [
            [tp - ut for tp, ut in zip(tp_list, ut_list)]
            for tp_list, ut_list in zip(time_points, usage_times)
        ]
        
        # Add the new key to the item
        item['time_points_2'] = time_points_2

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def process_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            process_json_file(file_path)

# Use the function
folder_path = 'FAILOVER_MUCH_INFO/kantoAnds'
folder_path = 'FAILOVER_MUCH_INFO/kantoEdgeTop'

folder_path = 'FAILOVER_MUCH_INFO/dtEdgeTop'
folder_path = 'FAILOVER_MUCH_INFO/dtAnds'
process_folder(folder_path)
