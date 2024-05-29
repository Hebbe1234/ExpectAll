import os
import json
import shutil

graphName = ["dt","kanto"]

source_dir = "no_change_mip"
pathToData =  source_dir #CHANGES ACCORDING TO WHAT DATA YOU LOOKING AT. 

#1splitIntoFolder.py
####ONLY SPLITS THE THINGS FROM THE RESULT FOLDER, INTO 4 FOLDERS
def split_into_folder_BDD(): 
    # Define the source and destination directories
    
    source_dir2 = source_dir + '/results'
    kanto_dir = source_dir+'/kantoMip'
    dt_dir = source_dir +'/dtMip'

    # Ensure destination directories exist
    os.makedirs(kanto_dir, exist_ok=True)
    os.makedirs(dt_dir, exist_ok=True)

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
                    shutil.copy(filepath, os.path.join(kanto_dir, filename))
                elif 'dt' in data["filename"]:
                    shutil.copy(filepath, os.path.join(dt_dir, filename))

    print("Files have been copied to the respective folders.")


# name = graphName + "Mip"
# data_folder = 'no_change_mip/'+name

# output_file = name+'.json'

# outfolder = name


def extract():
    for name in graphName: 
        file_name = name+"Mip"
        data_folder = source_dir+"/"+file_name
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
        with open(file_name+'.json', 'w') as f:
            json.dump(demands_and_all_times, f, indent=4)

def extractToMany():
    for name in graphName: 
        output_file = name+'Mip.json'
        data_folder = pathToData + "/" + name  #Filepath direclty to the json. 

        outfolder = name+"Mip"
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
split_into_folder_BDD()
time.sleep(0.3)
extract()
time.sleep(1)
extractToMany()
time.sleep(1)
