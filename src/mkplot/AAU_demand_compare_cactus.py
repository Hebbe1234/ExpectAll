import os
import json
import subprocess
import math
import argparse
from AAU_create_json_and_make_pdfs import extract_run_times, init_data, init_graph_metadata

parser = argparse.ArgumentParser("cactus")
parser.add_argument("--dir", type=str, default=[],required=True)
parser.add_argument("--legend", type=str, default=[],nargs="+")
parser.add_argument("--xaxis", type=int, default=0)

args = parser.parse_args()

data = {}
data = init_data(args.dir)
extract_run_times(args.dir, data,args.xaxis)
init_graph_metadata(data)          # now we have the runtime for all demands for given experiment

demands = list([int(d) for d in data.keys()])
demands.sort()
data = {int(d) : v for d,v in data.items()}

for i,d in enumerate(demands):
    data[d]["preamble"]["prog_alias"] = args.legend[i]

for demand, plot_data in data.items():
    file_name = f"json_folder/{demand}.json"
    with open(file_name, "w") as json_file:
        json.dump(plot_data, json_file, indent=4)

print("hi")
print("hi",demands)
xmin = 0
xmax = max([data[d]["meta"]["x_max"] for d in data])
ymin = min([data[d]["meta"]["y_min"] for d in data])
ymax = max([data[d]["meta"]["y_max"] for d in data])
print(xmin, xmax, ymin, ymax)

inputs = [f"json_folder/{demand}.json" for demand in demands]

command = [
    'python3',      
    'mkplot.py',    
    '--legend', 'prog_alias',
    '-t', '1000000',
    '-b', 'png',
    '--ylog',
    '--save-to', 'cactus_graphs/compare',
    '--xmax', str(xmax),
    '--ymin', str(ymin),
    '--ymax', str(ymax + 50),
    '--lloc', 'upper left',
    '--lncol', '4',
    *inputs
]

subprocess.run(command)
