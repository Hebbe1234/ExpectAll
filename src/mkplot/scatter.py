import pandas as pd
import csv
import matplotlib.pyplot as plt
import argparse
import os

parser = argparse.ArgumentParser("mainbdd.py")
parser.add_argument("-d", type=str, default="../../out/csv-data", help="directory of csv files to plot")
#parser.add_argument("-x", default="wavelength", type=str, help="x axis column")
#parser.add_argument("-y", default="CPU time", type=str, help="y axis")
parser.add_argument("-s", default=";", type=str, help="seperator")
parser.add_argument("-savedir", default="wavelength-data/", help="dir to store")
parser.add_argument("-savefile", help = "file name to store")
args = parser.parse_args()

if not os.path.isdir(args.savedir):
    os.makedirs(args.savedir)

for subdirs, dirs, files in os.walk(args.d):
    legend = []
    xlabel = ""
    ylabel = ""
    for file in files:
        if not file.endswith(".csv"):
            continue
        csvfile = subdirs + "/" + file
        df = pd.read_csv(csvfile, sep=args.s, encoding = "utf-8")
        
        xlabel = df.columns[0]
        ylabel = df.columns[1]

        df.rename(columns=lambda x: x.strip(), inplace=True)
        df.sort_values(by=[df.columns[0]], inplace=True)
        x = df.loc[:, df.columns[0]]
        y = df.loc[:, df.columns[1]]
        plt.plot(x,y)
        legend.append(file[4:-13])
    
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend(legend,bbox_to_anchor=(1.02, 1.0))

if args.savefile:
    plt.savefig(args.savedir+"/"+args.savefile, bbox_inches = "tight")
