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
args = parser.parse_args()

if not os.path.isdir(args.savedir):
    os.makedirs(args.savedir)
    os.makedirs("csv-"+args.savedir)

def plot(data, x_index, y_index, save_dest):
    xlabel = ""
    ylabel = ""
    for graph_name, (headers, rows) in data:

        newHeader = headers[0:3]
        newHeader.extend(["size","solutions"])
        newHeader.extend(headers[3:])
        headers = newHeader
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
    plt.xticks(range(math.ceil(xmin), math.ceil(xmax)))
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend(bbox_to_anchor=(1.02, 1.0))
    plt.savefig(save_dest, bbox_inches = "tight")
    plt.clf()



# data is dict from graph name to pair of headers and rows
data = convert_to_scatter_format(args.d)
num_graphs = 1 if args.split < 1 else math.ceil(len(data) / args.split)
for i in range(num_graphs):
    start = i*args.split
    plot_data = list(data.items())[start: start + args.split]
    plot(plot_data, args.x, args.y, f"{args.savedir}/{args.savefile}({i})")

