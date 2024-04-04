import pandas as pd
import csv
import matplotlib.pyplot as plt
import argparse
import os
from convert_to_csv import convert_to_scatter_format
import math
from mpl_toolkits import mplot3d
import numpy as np

parser = argparse.ArgumentParser("mainbdd.py")
parser.add_argument("-d", type=str, default="../../out/csv-data", help="directory of csv files to plot")
parser.add_argument("-x", default=0,type=int, help="x axis column")
parser.add_argument("-y", default=0, type=int, help="y axis")
parser.add_argument("-z", default=0, type=int, help="y axis")
parser.add_argument("-s", default=";", type=str, help="seperator")
parser.add_argument("-savedir", default="graphs/", help="dir to store")
parser.add_argument("-savefile", default="default_graph", help = "file name to store")
args = parser.parse_args()

if not os.path.isdir(args.savedir):
    os.makedirs(args.savedir)
    os.makedirs("csv-"+args.savedir)



xlabel = ""
ylabel = ""

plt.figure()
ax = plt.axes(projection="3d")

for graph_name, (headers, rows) in convert_to_scatter_format(args.d).items():
    xaxis = headers[args.x]
    yaxis = headers[args.y]
    zaxis = headers[args.z]

    df = pd.DataFrame(rows, columns=headers)
    df = df.sort_values(by=[xaxis])
    x = df.loc[:,xaxis]
    y = df.loc[:,yaxis]
    z = df.loc[:,zaxis]
    ax.scatter3D(x,y,z,marker="o", label=graph_name)
    xlabel = headers[args.x]
    ylabel = headers[args.y]
    zlabel = headers[args.z]
xmin, xmax = plt.xlim()
ymin, ymax = plt.ylim()
ax.axis([xmax, xmin, ymax, ymin])
plt.xticks(range(math.ceil(xmin), math.ceil(xmax)))
plt.xlabel(xlabel)
plt.ylabel(ylabel)
ax.set_zlabel(zlabel)
plt.legend(bbox_to_anchor=(1.02, 1.0))
plt.savefig(args.savedir+"/"+args.savefile, bbox_inches = "tight")
plt.show()

