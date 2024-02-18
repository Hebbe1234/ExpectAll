import os
import json
import subprocess
import math
import getopt
import sys
import argparse
from tarRead import parse_path

    
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
                    data[str(number_of_demands)] = {"stats":{},"preamble":{},"meta":{}}
        break
    return data

def get_run_time(lines,rtime_attr, true_only):
    if not lines:
            return None
        
    lines = [l for l in lines if l]

    if "True" not in lines[-1] and "False" not in lines[-1]:
        return None
    
    if true_only and "True" not in lines[-1]:
        return None
    
    data = list(map(str.strip, lines[-1].split(";")))

    return {
        "status": True,
        "rtime": float(data[rtime_attr]),
        "mempeak": "1 KiB"
    }

def make_graph_data(raw_data, data, rtime_attr=0, true_only=False):
    instance = 0
    for graph, demand_dict in raw_data.items():
        instance += 1
        for demand, lines in demand_dict.items():
            if demand not in data.keys():
                data.update({demand:{"stats":{},"preamble":{},"meta":{}}})
            instance_data = get_run_time(lines, rtime_attr, true_only)
            instance_name =  "".zfill(10) + str(instance) + "_" + graph

            if instance_data is not None:
                data[demand]["stats"][instance_name] = instance_data


# Define graphing metadata
def init_graph_metadata(data, label=""):
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
            "prog_alias": label
            }
        }
        section.update(preamble_info)
        section.update(meta_info)



if __name__ == "__main__":
    in_dirs = []

    parser = argparse.ArgumentParser("cactus")
    parser.add_argument("--dirs", type=str, default=[],nargs="+",)
    parser.add_argument("--legend", type=str, default=[],nargs="+")
    parser.add_argument("--xaxis", type=int, default=[], nargs="+")
    parser.add_argument("--savedest", type=str, default="cactus_graphs/")
    parser.add_argument("--select", type=int, default=[], nargs="+")
    parser.add_argument("--true_only", type=str, default="false")

    args = parser.parse_args()
    in_dirs=args.dirs
    legend_list=args.legend
    xaxis_list=args.xaxis
    demands_list=args.select
    true_only = args.true_only != "false"
    
    assert len(legend_list) == len(xaxis_list) and len(legend_list) == len(in_dirs) and (len(demands_list) == 0 or len(demands_list) == len(legend_list))

    print(in_dirs, legend_list, xaxis_list, demands_list)
    
    full_data = {}
    legend = {}
    rtime = {}

    for i,k in enumerate(in_dirs):
        legend[k] = legend_list[i]
        rtime[k] = xaxis_list[i]

    print(legend, rtime)
    
    if len(demands_list) > 0:
        full_data['0'] = {}    


    for i, out in enumerate(in_dirs):
        graph_data = {}
        data_directory = f"../../out/{out}"

        raw_data = parse_path(data_directory)
        make_graph_data(raw_data, graph_data, rtime[out], true_only)
    
        init_graph_metadata(graph_data, legend[out])          # now we have the runtime for all demands for given experiment

        
        if len(demands_list) == 0:
            for demands, _ in graph_data.items():
                if demands not in full_data:
                    full_data[demands] = {}
                    
                full_data[demands][out] = {}

            for demands, plot_data in graph_data.items():
                file_name = f"json_folder/{demands}_{out}.json"
                with open(file_name, "w") as json_file:
                    json.dump(plot_data, json_file, indent=4)
                full_data[demands][out] = plot_data

        else:
            full_data['0'][out] = {}

            
            for demands, plot_data in graph_data.items():            
                if int(demands) != int(demands_list[i]):
                    continue 
                
                file_name = f"json_folder/{0}_{out}.json"
                with open(file_name, "w") as json_file:
                    json.dump(plot_data, json_file, indent=4)
                
                full_data['0'][out] = plot_data

    for demand, in_dirs in full_data.items():
        xmax = 70
        ymax = 0
        ymin = 0
        xmin = 0
        
        
        stop = False
        for out in in_dirs:
            xmax = [in_dirs[out]["meta"]["x_max"] for out in in_dirs if in_dirs[out]["meta"]]
            ymax = [in_dirs[out]["meta"]["y_max"] for out in in_dirs if in_dirs[out]["meta"]]
            xmin = [in_dirs[out]["meta"]["x_min"] for out in in_dirs if in_dirs[out]["meta"]]
            ymin = [in_dirs[out]["meta"]["y_min"] for out in in_dirs if in_dirs[out]["meta"]]
            
            if not xmax or not ymax or not xmin or not ymin:
                stop = True
                continue
            xmax = max(xmax)
            ymax= min(3600, max(ymax))
            ymin = min(ymin)
            xmin = min(xmin)
        if stop:
            continue
        inputs = [f"./json_folder/{str(demand)}_{o}.json" for o in in_dirs if full_data[str(demand)][o]["stats"]]
        command = [
            'python3',      
            'mkplot.py',    
            '--legend', 'prog_alias',
            '-t', '1000000',
            '-b', 'svg',
            '--ylog',
            '--save-to', f'{args.savedest}demands'+str(demand) + '.svg',
            '--xmax', str(xmax),
            '--ymin', str(ymin),
            '--ymax', str(ymax + 50),
            '--lloc', 'lower right',
            '--lncol', '1',
            *inputs
        ]

        subprocess.run(command)


    

