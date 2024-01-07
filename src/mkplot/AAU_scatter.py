import pandas as pd
import csv
import matplotlib.pyplot as plt
import argparse
import os
from convert_to_csv import convert_to_scatter_format
import math
from pathlib import Path



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

if __name__ == "__main__":
    parser = argparse.ArgumentParser("mainbdd.py")
    parser.add_argument("-d", type=str, default="../../out/csv-data", help="directory of csv files to plot")
    parser.add_argument("-x", default=0,type=int, help="x axis column")
    parser.add_argument("-y", default=0, type=int, help="y axis")
    parser.add_argument("-s", default=";", type=str, help="seperator")
    parser.add_argument("-savedest", default="", help="dir to store")
    parser.add_argument("-agg", default=None, type=int)
    parser.add_argument("-xlabel",default="",type=str)
    parser.add_argument("-ylabel",default="",type=str)
    parser.add_argument("-agg_func",default="median",type=str)
    parser.add_argument("-xscaling",default=1,type=float)
    parser.add_argument("-scatter",default=False,type=bool)

    args = parser.parse_args()

    file = Path(args.savedest)
    file.parent.mkdir(parents=True, exist_ok=True)
    if not os.path.isdir(args.d):
        print("Directory does not exist: ",args.d)
        exit(0)
    
    df = pd.read_csv(args.d)

    # if args.agg >= 0:
    #     df, headers = aggregate(data, args.agg, args.x, args.agg_func)
    #     xlabel = args.xlabel if args.xlabel else headers[args.x]
    #     ylabel = args.ylabel if args.ylabel else headers[args.agg]