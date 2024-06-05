import os
import shutil
import json
source_dir = "EXPERIMENT_FAILOVER_RUN_FIX_1D_NOCHANGE"
pathToData =  source_dir #CHANGES ACCORDING TO WHAT DATA YOU LOOKING AT. 

#1splitIntoFolder.py
####ONLY SPLITS THE THINGS FROM THE RESULT FOLDER, INTO 4 FOLDERS
def split_into_folder_BDD(): 
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

def extract():
    for graphname in graphNames:
        for queryType in queryOptions: 
            name = graphname + queryType
            output_file = "table_data_"+name+'.json'
            data_folder = pathToData + "/" + name  #Filepath direclty to the json. 
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

                    demadns = data.get('demands')
                    query_impossible_count = data.get('query_impossible_count')
                    infeasable_count = data.get('no_change_query_infeasible_counts')
                    no_change_query_solved_counts = data.get('no_change_query_solved_counts')
                    no_change_query_not_solved_but_feasible_counts = data.get('no_change_query_not_solved_but_feasible_counts')
                    # Append demands and all_times to the list
                    demands_and_all_times.append({
                        'demands': demadns,
                        'query_impossible_count': query_impossible_count,
                        'infeasable_count': infeasable_count,
                        'no_change_query_solved_counts': no_change_query_solved_counts,
                        'no_change_query_not_solved_but_feasible_counts': no_change_query_not_solved_but_feasible_counts,
                    })

            with open(output_file, 'w') as f:
                json.dump(demands_and_all_times, f, indent=4)


split_into_folder_BDD()
import time
time.sleep(1)
extract()


