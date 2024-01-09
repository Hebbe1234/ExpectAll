import pandas as pd
import matplotlib.pyplot as mp
from itertools import permutations
import matplotlib.pyplot as plt
from bdd import BDD
from reordering import type_tuple_to_string

def gen_initial_df(types):
    rows = []

    with open("./topologies/10_over20.txt", mode="r") as files:
        for file in files:
            for oo in ["False", "True"]:
                    for gf in ["False", "True"]:
                        for i, t_p in enumerate(permutations(types)):
                            rows.append([file.replace("\n", ""), i, oo, gf, type_tuple_to_string(t_p, BDD.prefixes)])

    return pd.DataFrame(rows, columns=["File", "ID", "Group_P_By_Edge_Order","Generics_First", "Order"]) 

def plot(df, order_by, out_file=None):
    sorted_df = df.sort_values([*order_by])

    sorted_df.reset_index(inplace=True, drop=True)
    size_scale = 1_000_000
    sorted_df["Size"] = sorted_df["Size"] / size_scale

    cols = ["green", "blue", "red", "orange"]

    tt = sorted_df
    tt.reset_index(inplace=True, drop=True)

    ax = tt.plot(y=["Time"],  kind="line", figsize=(9, 8), color=cols[0])
    ax2 = ax.twinx()  
    tt.plot(y=["Size"],  kind="line", style="--", figsize=(9, 8), color=cols[1], ax=ax2)

    fs = 14
    
    if ax is not None:      
        ax.legend([])
        ax.set_xlabel("Variable order - Instance", fontsize=fs)
        ax.set_ylabel('Mean run time [s]', color=cols[0],fontsize=fs )  
        ax.tick_params(axis='y', labelcolor=cols[0])
        ax.set_ylim([0, 65])
        
        ax2.legend([])
        ax2.set_ylim([0, 4205000 / size_scale])
        ax2.set_ylabel('Mean size [Millions of nodes]', color=cols[1],fontsize=fs)  
        ax2.tick_params(axis='y', labelcolor=cols[1])
 
    print(sorted_df[sorted_df["Order"] == "Default_Good"]) 
    ax.plot(sorted_df[sorted_df["Order"] == "Default_Good"].index.tolist()[0], sorted_df[sorted_df["Order"] == "Default_Good"]["Time"], marker=6, markersize=10, markeredgecolor="green", markerfacecolor="green", zorder=200)
    ax2.plot(sorted_df[sorted_df["Order"] == "Default_Good"].index.tolist()[0], sorted_df[sorted_df["Order"] == "Default_Good"]["Size"], marker=7, markersize=10, markeredgecolor="blue", linestyle=":",markerfacecolor="blue", zorder=20)
        
    if out_file is not None:
        plt.savefig(f"../out/{out_file}.pdf", bbox_inches='tight')
        
    mp.show()
    
    sorted_df["Order"] = sorted_df["Order"].apply(lambda o: ",".join([f"\\v{{{c}}}" for c in o]))
    print(f"Best by {order_by}")
    print(sorted_df.head())
    
    print(f"Worst but no time out {order_by}")
    print(sorted_df[sorted_df["Time"] < 60].tail())
    
    print(f"Worst by {order_by}")
    print(sorted_df.tail())
   
def main(results_file, pkl_file, types):
    if results_file != "" and results_file is not None:
        results = pd.read_csv(results_file, delimiter=";")
        results.to_pickle(pkl_file)
        
    df = pd.read_pickle(pkl_file)
    
    df.columns = ["File", "ID", "Group_P_By_Edge_Order", "Generics_First", "Order", "Size", "Time"]
    df.Group_P_By_Edge_Order = df.Group_P_By_Edge_Order.astype(str).str.strip()
    df.Generics_First = df.Generics_First.astype(str).str.strip()
    
    init_df = gen_initial_df(types)
 
    full_df = init_df.merge(df, left_on=["File", "ID", "Group_P_By_Edge_Order", "Generics_First"], right_on=["File", "ID", "Group_P_By_Edge_Order","Generics_First"], how="left")
    
    full_df["Size"].fillna(4000000, inplace=True)
    full_df["Time"].fillna(60, inplace=True)
    full_df["Order"] = full_df["Order_x"]
    
    if len(types) == 7:
        # Add default heuristics to the result set
        list1 = ["Default(Good)", 0, "--", "--", "Default_Good", "Default_Good",  33573.6, 5.617416546, "Default_Good"]
        list2 = ["Default(Bad)", 0, "--", "--", "Default_Bad", "Default_Bad", 25088.3, 6.278287 , "Default_Bad"]
        full_df.loc[len(full_df)] = list1
        full_df.loc[len(full_df)] = list2
    else:
         # Add default heuristics to the result set
        list1 = ["Default(Good)", 0, "--", "--", "Default_Good", "Default_Good",  4000000, 60, "Default_Good"]
        list2 = ["Default(Bad)", 0, "--", "--", "Default_Bad", "Default_Bad", 4000000, 60 , "Default_Bad"]
        full_df.loc[len(full_df)] = list1
        full_df.loc[len(full_df)] = list2
        
    print(len(full_df["Order"].unique()))    

    times = full_df[["Group_P_By_Edge_Order", "Generics_First", "Order", "Time", "Size"]].groupby(["Group_P_By_Edge_Order", "Generics_First", "Order"], as_index=False).mean()
    times.reset_index(inplace=True, drop=True)
    

    plot(times, ["Time", "Size"], "var_ords_time_then_size")

if __name__ == "__main__":
    types_baseline = [BDD.ET.LAMBDA, BDD.ET.DEMAND,  BDD.ET.EDGE, BDD.ET.SOURCE, BDD.ET.TARGET, BDD.ET.NODE, BDD.ET.PATH]
    types_edge_encoding = [BDD.ET.DEMAND,  BDD.ET.EDGE, BDD.ET.SOURCE, BDD.ET.TARGET, BDD.ET.NODE, BDD.ET.PATH]
    
    main("../out/old/results.csv", "../out/old/results_baseline.pkl", types_baseline)
    # main("../out/old/results_edge_encoding.csv", "../out/old/results_edge_encoding.pkl", types_edge_encoding)