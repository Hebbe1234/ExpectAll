import argparse
import os    

parser = argparse.ArgumentParser("mainbdd.py")
parser.add_argument("-dir", type=str, help="output directory to graph")
parser.add_argument("-type", type=str, help="scatter, cactus")
args = parser.parse_args()

for subdirs, _, files in os.walk(args.dir):
    for file in files:
        print(subdirs + "/" + file)
                
    #for file in files:
     #   if not file.endswith(".csv"):
      #      continue
       # csvfile = subdirs + "/" + file

#def to_scatter_csv():
