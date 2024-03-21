import pandas as pd
import csv
import matplotlib.pyplot as plt
import argparse
import os
from convert_to_csv import convert_to_scatter_format
import math
from pathlib import Path



def plotdf(df, xlabel, ylabel, x, y, save_dest, isScatter=False, xscaling=1, yscaling=1, title=""):
    
    #df = df.sort_values(by=[x])
    x = df.loc[:,x].apply(lambda x: x*xscaling)
    y = df.loc[:,y].apply(lambda x: x*yscaling) 

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


def aggregate(df: pd.DataFrame, agg_id, x_id, agg_func="median"):
    f = {df.columns[agg_id]: agg_func}
    df = df.groupby([df.columns[x_id]], as_index=False).agg(f)
    return df

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
    parser.add_argument("-yscaling",default=1,type=float)
    parser.add_argument("-title",default="",type=str)

    args = parser.parse_args()

    file = Path(args.savedest)
    file.parent.mkdir(parents=True, exist_ok=True)
    if not os.path.isfile(args.d):
        print("file does not exist: ",args.d)
        exit(0)
    
    df = pd.read_csv(args.d)
    header = df.columns
    df = aggregate(df, args.agg, args.x, args.agg_func)
    plotdf(df, args.xlabel, args.ylabel, header[args.x], header[args.agg], args.savedest, args.scatter, args.xscaling, args.yscaling, args.title)

