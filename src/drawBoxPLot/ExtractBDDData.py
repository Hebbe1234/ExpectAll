import os
import shutil
import json
import time

####ONLY SPLITS THE THINGS FROM THE RESULT FOLDER, INTO 4 FOLDERS
def split_into_folder_BDD(source_dir): 
    # Define the source and destination directories
    
    source_dir2 = source_dir + '/results'
    kanto_dynamic_dir = source_dir+'/kantoAnds'
    kanto_failover_dir = source_dir+ '/kantoEdgeTop'
    dt_dynamic_dir = source_dir +'/dtAnds'
    dt_failover_dir = source_dir+'/dtEdgeTop'

    # Ensure destination directories exist
    os.makedirs(kanto_dynamic_dir, exist_ok=True)
    os.makedirs(kanto_failover_dir, exist_ok=True)
    os.makedirs(dt_dynamic_dir, exist_ok=True)
    os.makedirs(dt_failover_dir, exist_ok=True)

    # Iterate through each file in the source directory
    for filename in os.listdir(source_dir2):
        if filename.endswith('.json'):
            filepath = os.path.join(source_dir2, filename)

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



graphNames = ["dt","kanto"]
queryOptions = ["Ands","EdgeTop"]

def extract(source_dir):
    for graphname in graphNames:
        for queryType in queryOptions: 
            name = graphname + queryType
            output_file = source_dir+name+'.json'
            # data_folder = pathToData + "/" + name  #Filepath direclty to the json. #IS THIS CORRECT 
            data_folder = source_dir + "/" + name  #Filepath direclty to the json. 
            outfolder = name

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
                    subtree_times = data.get('subtree_times')
                    no_change_query_solved_times = data.get('no_change_query_solved_times')
                    no_change_query_times = data.get('no_change_query_times')
                    # Append demands and all_times to the list
                    demands_and_all_times.append({
                        'demands': demands,
                        'all_times': all_times,
                        'subtree_times': subtree_times,
                        'no_change_query_solved_times': no_change_query_solved_times,
                        'no_change_query_times': no_change_query_times
                    })

                                # Write the extracted data to a new JSON file
            with open(output_file, 'w') as f:
                json.dump(demands_and_all_times, f, indent=4)


def extractToMany(source_dir):
    for graphname in graphNames:
        for queryType in queryOptions: 
            name = graphname + queryType


            output_file = source_dir+name+'.json'
            # data_folder = pathToData + "/" + name  #Filepath direclty to the json. 
            outfolder = source_dir+"_"+name
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
                        "all_times": [item["all_times"][i]],
                        "subtree_times": [item["subtree_times"][i]],
                        "no_change_query_solved_times": [item["no_change_query_solved_times"][i]],
                        "no_change_query_times": [item["no_change_query_times"][i]],

                    }
                    new_data.append(new_item)
                
                # Write new data to a new JSON file in the json2 folder
                with open(outfolder+f'/EdgeFailover_{i+1}.json', 'w') as outfile:
                    json.dump(new_data, outfile, indent=4)



source_dirs = ["../../out/Reproduceability/EXPERIMENT_FAILOVER_RUN_FIX_1D_NOCHANGE"]
for dir in source_dirs: 
    split_into_folder_BDD(dir)
    time.sleep(0.3)
    extract(dir)
    time.sleep(0.3)
    extractToMany(dir)
    time.sleep(0.3)
