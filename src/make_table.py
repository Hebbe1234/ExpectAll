import json
import os
import csv
import pandas as pd
import math

def find_nicest_number(seconds):
	seconds = math.ceil(seconds)
	if seconds < 60:
		return f"{seconds}s"
	
	minutes = math.ceil(seconds / 60.0)
	if minutes < 60:
		return f"{minutes}m"
	
	hours = math.ceil(seconds / (60.0*60.0))
	if hours < 24:
		return f"{hours}h"
	
	days = math.ceil(seconds / (60*60*24))
	if days < 365:
		return f"{days}d"
	
	years = math.ceil(seconds / (60*60*24*365))
	return f"{years}y"
	
	
	
	

def convert(row):
	x_string = find_nicest_number(row["solve_time_x"])
	y_string = find_nicest_number(row["solve_time_y"])
	return x_string + "/" + y_string

df = pd.read_json("../out/EXPERIMENT_FAILOVER_MIP_FINAL_RUN_1_PRECOMP_FULL/results/pre_comps.json")

df["topology"] = df["filename"].replace("\\", "/").str.replace(".gml", "").str.split("/").str[-1]

legal_columns = ["demands", "topology", "solve_time", "par5"]
df = df.drop([c for c in df.columns if c not in legal_columns], axis=1)
df = df[df["demands"].isin([3,6,9])]

groupby_columns = ["demands","par5"]

df = df.merge(df, on=groupby_columns)

df = df[(df["topology_x"] == "dt") & (df["topology_y"] == "kanto11")]

df["dt/kanto"] = df.apply(lambda row: convert(row),axis=1)

df["failures"] = df["par5"]
legal_columns = ["demands", "failures","dt/kanto"]
df = df.drop([c for c in df.columns if c not in legal_columns], axis=1)

df.to_csv("./mip_full.csv", index=False)


# uniq_df = df.drop(["topology","solve_time"], axis=1,inplace=False)

# uniq_df.drop_duplicates(subset=groupby_columns, keep="first",inplace=True)

# sub_dfs = []

# for _, row in uniq_df.iterrows():
# 	sub_df = df
# 	for c in groupby_columns:
# 		sub_df = sub_df[sub_df[c] == row[c]]




