import os
import json

folder_path = 'EXPERIMENT_FAILOVER_BDD_RUN_4/results'


def process_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        
        for item in data:
            if "failover_plus_build_time" in item:
                failover_plus_build_time = item["failover_plus_build_time"]
                if "solve_time" in item:
                    item["solve_time"] = failover_plus_build_time

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def process_all_json_files(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                process_json_file(file_path)

process_all_json_files(folder_path)