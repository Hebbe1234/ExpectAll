import argparse
import os    
import pandas as pd
import csv
from pathlib import Path

def parse_type(x: str):
    if "." in x and x.replace(".","").isnumeric():
        return float(x)
    elif x.isdigit():
        return int(x)
    return x

def get_header_and_rows(dir):
    headers = []
    rows = []
    first = True

    for subdirs, _, files in os.walk(dir):
        for output in files:
            with open(f"{subdirs}/{output}", "r") as f:
                lines = list(map(lambda x: x.strip().lower(), f.readlines()))
                if lines is None or lines == [] : 
                    continue
                data = lines[-1]
                if "true" not in data and "false" not in data:
                    continue
                if first:
                    headers = lines[-2].split(";")
                rows.append(list(map(parse_type, data.split(";"))))
    return headers, rows                
    
def pad_data(data, pad, x:int):
    
    num_x_values = 0
    x_values = []

    # find all different values of x
    for graph, (headers, rows) in data.items():
        num_x_values = max(num_x_values, len(rows))
        if num_x_values == len(rows):
            x_values = [row[x] for row in rows]
            x_values.sort()

    # for each x value that needs a y value, do fill 
    for graph, (headers, rows) in data.items():
        for value in x_values:
            if value in [row[x] for row in rows]:
                continue
            
            pad_row = [pad for i in range(len(headers))]
            pad_row[x] = value
            rows.append(pad_row)
        data[graph] = (headers, rows)

    return data

def convert_to_scatter_format(dir, xid):
    data = {}
    headers = []
    for subdirs, dirs, files in os.walk(dir):
        if not files:
            continue
        header, rows = get_header_and_rows(subdirs)
        if header and rows:
            headers = header
            graph_name = subdirs.split("/")[-1]
            rows = sorted(rows, key=lambda row: row[xid])
            data[graph_name] = (header, rows)
    return data, headers

def filter_max_data(data, xmax, xid):
    data = {graph:(headers, rows) for graph, (headers, rows) in data.items() if len(rows)>0 and rows[-1][xid] == xmax}
    return data

if __name__ == "__main__":

    parser = argparse.ArgumentParser("mainbdd.py")
    parser.add_argument("-dir", type=str, help="output directory to graph")
    parser.add_argument("-yfill", type=int ,default=0, help="value to fill missing y values")
    parser.add_argument("-savedest",type=str, help="dest to save file")
    parser.add_argument("-x", type=int, default=0, help="index of x column")
    parser.add_argument("-xmax",type=int, default=0, help="max value on x axis")
    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        print("Directory does not exist: ",args.dir)
        exit(0)
    file = Path(args.savedest)
    file.parent.mkdir(parents=True, exist_ok=True)
    
    data, headers = convert_to_scatter_format(args.dir, args.x)
    headers = [header.strip() for header in headers]

    if args.xmax:
        data = filter_max_data(data, args.xmax, args.x)

    if args.yfill:
        data = pad_data(data, args.yfill, args.x)
    
    
    writer = csv.writer(open(args.savedest, "w"), delimiter=",")
    writer.writerow(headers + ["graph"])
    for graph,(_,rows) in data.items():
        for row in rows:
            r = row + [graph]
            writer.writerow(r)