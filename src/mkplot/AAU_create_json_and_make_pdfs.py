import os
import json
import subprocess
import math

# Extract solve times from output files, if they were solved
def parse_txt_file(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()

    #if  lines and "solve" in lines[-1]:
     #   solve_time = map(str.strip, lines[-1].split(":"))
    if not lines:
        return None
    
    solve_time, all_time, solveable = map(str.strip, lines[-1].split(","))

    if solveable:
        return {
            "status": True,
            "rtime": float(solve_time),
            "mempeak": "1 KiB"
        }
    else:
        return None
    
# initialize data for each run of demands. Demands are given in the names of the output files.
def init_data(data_directory):
    data = {}

    for root, graph_dirs,_ in os.walk(data_directory):
        for graph_dir in graph_dirs:
            directory_path = os.path.join(root, graph_dir)
            
            # Iterate through files in the subdirectory
            for output in os.listdir(directory_path):
                if output.endswith(".txt"):
                    number_of_demands = output.split("output")[1].split(".txt")[0]
                    data[str(number_of_demands)] = {"stats":{}}
            break
        break
    return data

# Extract running times for each graph for each demand
def extract_run_times(data_directory,data):
    for root, graph_dirs, _ in os.walk(data_directory):
        instance = 0
        for graph_dir in graph_dirs:
            instance += 1
            directory_path = os.path.join(root, graph_dir)
            for output in os.listdir(directory_path):
                output_path = os.path.join(directory_path,output)

                number_of_demands = output.split("output")[1].split(".txt")[0]
                instance_name = os.path.splitext("instance"+str(instance))[0]
                instance_data = parse_txt_file(output_path)

                if instance_data is not None:
                    data[str(number_of_demands)]["stats"][instance_name] = instance_data

# Define graphing metadata
def init_graph_metadata(data):
    for key, section in data.items():
        if not section["stats"]: #if all runs timed out
            continue

        y_min,y_max,x_min,x_max = math.inf,0,0,0
        for k,d in section.items():
            
            for j, l in d.items(): 
                if l["rtime"] > y_max : 
                    y_max = l["rtime"]
                if l["rtime"] < y_min : 
                    y_min = l["rtime"]
                x_max += 1

        meta_info = {
            "meta":{
                "y_min": y_min, 
                "y_max": y_max,
                "x_min": x_min,
                "x_max": x_max
            }
        }
        preamble_info = {
        "preamble": {
            "benchmark": "ttt" ,
            "prog_args": None,
            "program": "another-good-tool",
            "prog_alias": "number of demands" + str(key)
            }
        }

        section.update(preamble_info)
        section.update(meta_info)


out_dirs = ["mip", "mytest2"]
full_data = {}

for out in out_dirs:
    data = {}
    data_directory = f"../../out/{out}" #TODO Change this so it points the correct way :)
    data = init_data(data_directory)
    extract_run_times(data_directory, data)
    init_graph_metadata(data)

    for demands, _ in data.items():
        full_data[demands] = {}

    for demands, plot_data in data.items():
        file_name = f"json_folder/{demands}_{out}.json"
        with open(file_name, "w") as json_file:
            json.dump(plot_data, json_file, indent=4)
        full_data[demands].update({out:plot_data})

exit()
for demand, out_dirs in full_data.items():
    # xmax = []
    # ymax = []
    # ymin = []
    # xmin = []
    
    
    for out in out_dirs:
        if not out_dirs[out]["stats"]:
            break
        xmax = [out_dirs[out]["meta"]["x_max"] for out in out_dirs if "meta" in out_dirs[out].keys()]
        ymax = [out_dirs[out]["meta"]["y_max"] for out in out_dirs if "meta" in out_dirs[out].keys()]
        xmin = [out_dirs[out]["meta"]["x_min"] for out in out_dirs if "meta" in out_dirs[out].keys()]
        ymin = [out_dirs[out]["meta"]["y_max"] for out in out_dirs if "meta" in out_dirs[out].keys()]
        
        xmax = max(xmax)
        ymax= max(ymax)
        ymin = min(ymin)
        xmin = min(xmin)
    print(xmax, ymax, ymin, xmin)
    command = [
        'python3',      # The Python interpreter
        'mkplot.py',    # The script you want to run
        '--legend', 'prog_alias',
        '-t', '1000000',
        '-b', 'pdf',
        '--ylog',
        '--save-to', 'demands'+str(demand) + '.pdf',
        '--xmax', str(xmax),
        '--ymin', str(ymin),
        '--ymax', str(ymax),
        '--lloc', 'lower right',
        f"./json_folder/*_mip.json"
    ]
    subprocess.run(command)


    

