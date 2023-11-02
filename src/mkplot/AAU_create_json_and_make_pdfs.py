import os
import json
import subprocess
import math
import getopt
import sys

# Extract solve times from output files, if they were solved
def parse_txt_file(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()

    #if  lines and "solve" in lines[-1]:
     #   solve_time = map(str.strip, lines[-1].split(":"))
    if not lines:
        return None
    
    if "True" not in lines[-1] and "False" not in lines[-1]:
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
    return data

# Extract running times for each graph for each demand
def extract_run_times(data_directory,data):
    for root, graph_dirs, _ in os.walk(data_directory):
        instance = 0
        for graph_dir in graph_dirs:
            directory_path = os.path.join(root, graph_dir)
            for output in os.listdir(directory_path):
                instance += 1
                output_path = os.path.join(directory_path,output)

                number_of_demands = output.split("output")[1].split(".txt")[0]
                instance_name = os.path.splitext("instance"+str(instance))[0]
                instance_data = parse_txt_file(output_path)

                if instance_data is not None:
                    if not str(number_of_demands) in data:
                        continue
                                        
                    data[str(number_of_demands)]["stats"][instance_name] = instance_data
# Define graphing metadata
def init_graph_metadata(data, label):
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
            "prog_alias": f"{label}, {key}"
            }
        }

        section.update(preamble_info)
        section.update(meta_info)




if __name__ == "__main__":
    out_dirs = []

    try: 
        opts, out_dirs = getopt.getopt(sys.argv[1:],'', [])
    
    except getopt.GetoptError as err:
        sys.stderr.write(str(err).capitalize() + '\n')
        sys.exit(1)
    
    full_data = {}

    for out in out_dirs:
        data = {}
        data_directory = f"../../out/{out}" #TODO Change this so it points the correct way :)
        data = init_data(data_directory)
        extract_run_times(data_directory, data)
        init_graph_metadata(data, out)

        for demands, _ in data.items():
            if demands not in full_data:
                full_data[demands] = {}
                
            full_data[demands][out] = {}

        for demands, plot_data in data.items():
            file_name = f"json_folder/{demands}_{out}.json"
            with open(file_name, "w") as json_file:
                json.dump(plot_data, json_file, indent=4)
            full_data[demands][out] = plot_data

    for demand, out_dirs in full_data.items():
        xmax = 70
        ymax = 0
        ymin = 0
        xmin = 0
        
        cancel = False
        for out in out_dirs:
            if not out_dirs[out]["stats"]:
                cancel = True
                break
            
            xmax = [out_dirs[out]["meta"]["x_max"] for out in out_dirs if "meta" in out_dirs[out].keys()]
            ymax = [out_dirs[out]["meta"]["y_max"] for out in out_dirs if "meta" in out_dirs[out].keys()]
            xmin = [out_dirs[out]["meta"]["x_min"] for out in out_dirs if "meta" in out_dirs[out].keys()]
            ymin = [out_dirs[out]["meta"]["y_min"] for out in out_dirs if "meta" in out_dirs[out].keys()]
            
            xmax = max(xmax)
            ymax= max(ymax)
            ymin = min(ymin)
            xmin = min(xmin)

        if cancel:
            continue
                
        inputs = [f"./json_folder/{str(demand)}_{o}.json" for o in out_dirs]
        command = [
            'python3',      # The Python interpreter
            'mkplot.py',    # The script you want to run
            '--legend', 'prog_alias',
            '-t', '1000000',
            '-b', 'svg',
            '--ylog',
            '--save-to', 'demands'+str(demand) + '.svg',
            '--xmax', str(xmax),
            '--ymin', str(ymin),
            '--ymax', str(ymax + 50),
            '--lloc', 'lower right',
            *inputs
        ]

        subprocess.run(command)


    

