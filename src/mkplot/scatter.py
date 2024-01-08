import pandas as pd
import csv
import matplotlib.pyplot as plt
import argparse
import os
from convert_to_csv import convert_to_scatter_format
import math

parser = argparse.ArgumentParser("mainbdd.py")
parser.add_argument("-d", type=str, default="../../out/csv-data", help="directory of csv files to plot")
parser.add_argument("-x", default=0,type=int, help="x axis column")
parser.add_argument("-y", default=0, type=int, help="y axis")
parser.add_argument("-s", default=";", type=str, help="seperator")
parser.add_argument("-savedir", default="graphs/", help="dir to store")
parser.add_argument("-savefile", default="default_graph", help = "file name to store")
parser.add_argument("-split", default=9, type=int, help = "if all graphs on same: -1")
parser.add_argument("-agg", default=None, type=int)
parser.add_argument("-pad", default=0, type=int)
parser.add_argument("-xlabel",default="",type=str)
parser.add_argument("-ylabel",default="",type=str)
parser.add_argument("-agg_func",default="median",type=str)
parser.add_argument("-xscaling",default=1,type=float)
parser.add_argument("-scatter",default=False,type=bool)

args = parser.parse_args()

if not os.path.isdir(args.savedir):
    os.makedirs(args.savedir)
    os.makedirs("csv-"+args.savedir)

if not os.path.isdir(args.d):
    print("Directory does not exist: ",args.d)
    exit(0)

def plotdf(df, xlabel, ylabel, x, y, save_dest, isScatter=False, xscaling=1, yscaling=1):

    df = df.sort_values(by=[x])
    x = df.loc[:,x].apply(lambda x: x*xscaling)
    y = df.loc[:,y]
    
    if isScatter:
        plt.scatter(x,y)
    else:
        plt.plot(x,y,marker="o", ms=5)

    xmin, xmax = plt.xlim()
    #plt.xticks(range(max(0,math.ceil(xmin)), math.ceil(xmax)))
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend(bbox_to_anchor=(1.02, 1.0))
    plt.savefig(save_dest, bbox_inches = "tight")
    plt.clf()
    print(save_dest)
    
def plot(data, x_index, y_index, save_dest):
    xlabel = ""
    ylabel = ""
    for graph_name, (headers, rows) in data:

        xaxis = headers[x_index]
        yaxis = headers[y_index]

        df = pd.DataFrame(rows, columns=headers)
        df = df.sort_values(by=[xaxis])
        x = df.loc[:,xaxis]
        y = df.loc[:,yaxis]

        plt.plot(x,y,marker="o", ms=5, label=graph_name)

        xlabel = headers[x_index]
        ylabel = headers[y_index]
    #xmin, xmax = plt.xlim()
    #plt.xticks(range(max(0,math.ceil(xmin)), math.ceil(xmax)))
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend(bbox_to_anchor=(1.02, 1.0))
    plt.savefig(save_dest, bbox_inches = "tight")
    plt.clf()

# for a given attribute we want to aggregate:
#   For each value of that attribute
#       Find row consisting of values from each graph
def aggregate(data: dict[str, tuple[list ,list]], agg, x, agg_func = "median"):    
    headers = []
    first = True
    df = pd.DataFrame()

    for graph, (headers, rows) in data.items():
        if first:
            headers=headers
            first = False
        df2 = pd.DataFrame(rows)
        df = pd.concat([df, df2], ignore_index=True)
        df.reset_index()
    f = {agg : agg_func}
    df = df.groupby(x, as_index=False).agg(f)
    
    return df, headers

def pad_data(data, pad, agg, x:int):
    
    num_x_values = 0
    x_values = []
    for graph, (headers, rows) in data.items():
        num_x_values = max(num_x_values, len(rows))
        if num_x_values == len(rows):
            x_values = [row[x] for row in rows]
            x_values.sort()
        
    for graph, (headers, rows) in data.items():
        for i in range(len(rows), num_x_values):   #loop through remaining x-values that need a  y-value
            pad_row = [pad for i in range(len(headers))]
            pad_row[x] = x_values[i]
            rows.append(pad_row)
        data[graph] = (headers, rows)

    return data


# data is dict from graph name to pair of headers and rows
data, headers = convert_to_scatter_format(args.d, args.x)
if args.pad:
    data = pad_data(data, args.pad, args.agg, args.x)

if args.agg >= 0:
    df, headers = aggregate(data, args.agg, args.x, args.agg_func)
    xlabel = args.xlabel if args.xlabel else headers[args.x]
    ylabel = args.ylabel if args.ylabel else headers[args.agg]
    plotdf(df, xlabel, ylabel, args.x,args.agg,f"{args.savedir}{args.savefile}",args.scatter,args.xscaling)
else:
    num_graphs = 1 if args.split < 1 else math.ceil(len(data) / args.split)
    for i in range(num_graphs):
        start = i*args.split
        plot_data = list(data.items())[start: start + args.split]
        plot(plot_data, args.x, args.y, f"{args.savedir}/{args.savefile}({i})")

