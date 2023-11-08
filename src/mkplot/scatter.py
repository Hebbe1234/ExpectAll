import pandas as pd
import csv
import matplotlib.pyplot as plt
import argparse
import os

parser = argparse.ArgumentParser("mainbdd.py")
parser.add_argument("-d", type=str, default="../../out/csv-data", help="directory of csv files to plot")
parser.add_argument("-x", default="wavelength", type=str, help="x axis column")
parser.add_argument("-y", default="CPU time", type=str, help="y axis")
parser.add_argument("-s", default=";", type=str, help="seperator")
parser.add_argument("-savedir", default="wavelength-data/", help="dir to store")
parser.add_argument("-savefile", help = "file name to store")
args = parser.parse_args()

for subdirs, dirs, files in os.walk(args.d):
    for file in files:
        if not file.endswith(".csv"):
            continue
        csvfile = subdirs + "/" + file
        df = pd.read_csv(csvfile, sep=args.s, encoding = "utf-8")
        df.rename(columns=lambda x: x.strip(), inplace=True)
        df.sort_values(by=[args.x], inplace=True)
        x = df[args.x]
        y = df[args.y]
        if not os.path.isdir(args.savedir):
            os.makedirs(args.savedir)
        plt.xlabel(args.x)
        plt.ylabel(args.y)
        plt.plot(x,y)
        
        #plt.savefig(args.savedir + file.replace(".","").replace("res_", "").replace("gml","").replace("csv", ""))
if args.savefile:
    plt.savefig(args.savefile)