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
parser.add_argument("-agg", default=None, type=list)
args = parser.parse_args()

if not os.path.isdir(args.savedir):
    os.makedirs(args.savedir)
    os.makedirs("csv-"+args.savedir)

if not os.path.isdir(args.d):
    print("Directory does not exist: ",args.d)
    exit(0)

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
    xmin, xmax = plt.xlim()
    #plt.xticks(range(max(0,math.ceil(xmin)), math.ceil(xmax)))
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend(bbox_to_anchor=(1.02, 1.0))
    plt.savefig(save_dest, bbox_inches = "tight")
    plt.clf()

# for a given attribute we want to aggregate:
#   For each value of that attribute
#       Find row consisting of values from each graph
def aggregate(data: dict[str, tuple[list ,list]], agg_list, x):
    aggregated = {"aggregated": None}
    
    agg_headers = []
    agg_row = [0 for i in range(len(agg_list))]
    headers = []

    first = True
    df = pd.DataFrame()
    for graph, (headers, rows) in data.items():
        if first:
            agg_headers = [i for i,h in enumerate(headers) if str(i) in agg_list]
            headers=headers
            first = False
        df2 = pd.DataFrame(rows)
        df = pd.concat([df, df2], ignore_index=True)
        df.reset_index()

    f = {int(i) : "mean" for i in agg_list}
    df = df.groupby(x, as_index=False).agg(f)
    xaxis = headers[x]
    yaxis = headers[int(agg_list[0])]

    x = df.loc[:,x]
    y = df.loc[:, int(agg_list[0])]

    plt.plot(x,y,marker="o", ms=5, label="something")
    plt.savefig(".", bbox_inches = "tight")

    #df.columns = agg_headers
    #print(df)
    return aggregated
    

# data is dict from graph name to pair of headers and rows
data = convert_to_scatter_format(args.d)
if args.agg:
    aggregated = aggregate(data, args.agg, args.x)
else:
    num_graphs = 1 if args.split < 1 else math.ceil(len(data) / args.split)
    for i in range(num_graphs):
        start = i*args.split
        plot_data = list(data.items())[start: start + args.split]
        plot(plot_data, args.x, args.y, f"{args.savedir}/{args.savefile}({i})")

