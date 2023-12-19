from matplotlib import axes
import pandas as pd
import matplotlib.pyplot as mp
from itertools import permutations
import itertools
import matplotlib.pyplot as plt
from itertools import chain, combinations
from bdd import BDD
from reordering import type_tuple_to_string


def all_subsets(ss):
    return chain(*map(lambda x: combinations(ss, x), range(0, len(ss)+1)))

def gen_initial_df():
    types = [BDD.ET.LAMBDA, BDD.ET.DEMAND,  BDD.ET.EDGE, BDD.ET.SOURCE, BDD.ET.TARGET, BDD.ET.NODE, BDD.ET.PATH]
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
    print(sorted_df[sorted_df["Order"] == "Default_Good"])

    cols = ["green", "blue", "red", "orange"]

    tt = sorted_df
    tt.reset_index(inplace=True, drop=True)

    ax = tt.plot(y=["Time"],  kind="line", figsize=(9, 8), color=cols[0])
    ax2 = ax.twinx()  
    tt.plot(y=["Size"],  kind="line", style="--", figsize=(9, 8), color=cols[1], ax=ax2)

    
    if ax is not None:
        # ax.set_title(f"Variable ordering comparison")
        
        ax.legend([])
        ax.set_xlabel("Variable order - Instance")
        ax.set_ylabel('Mean build time [s]', color=cols[0])  
        ax.tick_params(axis='y', labelcolor=cols[0])
        ax.set_ylim([0, 65])
        
        ax2.legend([])
        ax2.set_ylim([0, 4005000 / size_scale])
        ax2.set_ylabel('Mean size [Millions of nodes]', color=cols[1])  
        ax2.tick_params(axis='y', labelcolor=cols[1])


    
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
    
    
   
def main():
    
    results = pd.read_csv("../out/results.csv", delimiter=";")
    results.to_pickle("../out/results.pkl")
    df = pd.read_pickle("../out/results.pkl")
    
    
    df.columns = ["File", "ID", "Group_P_By_Edge_Order", "Generics_First", "Order", "Size", "Time"]
    df.Group_P_By_Edge_Order = df.Group_P_By_Edge_Order.astype(str).str.strip()
    df.Generics_First = df.Generics_First.astype(str).str.strip()
    
    
    
    init_df = gen_initial_df()
 
    full_df = init_df.merge(df, left_on=["File", "ID", "Group_P_By_Edge_Order", "Generics_First"], right_on=["File", "ID", "Group_P_By_Edge_Order","Generics_First"], how="left")
    
    full_df["Size"].fillna(4000000, inplace=True)
    full_df["Time"].fillna(60, inplace=True)
    full_df["Order"] = full_df["Order_x"]
    
    print(full_df.columns)
    list1 = ["Default(Good)", 0, "--", "--", "Default_Good", "Default_Good",  33573.6, 5.617416546, "Default_Good"]
    list2 = ["Default(Bad)", 0, "--", "--", "Default_Bad", "Default_Bad", 25088.3, 6.278287 , "Default_Bad"]
    full_df.loc[len(full_df)] = list1
    full_df.loc[len(full_df)] = list2
    
    print(len(full_df["Order"].unique()))    
    #df = pd.read_pickle("../out/Reordering_csvs/df_small.pkl")

    times = full_df[["Group_P_By_Edge_Order", "Generics_First", "Order", "Time", "Size"]].groupby(["Group_P_By_Edge_Order", "Generics_First", "Order"], as_index=False).mean()
    times.reset_index(inplace=True, drop=True)
    
    
    plot(times, ["Time", "Size"], "var_ords_time_then_size")
    # plot(times, ["Time", "Size"], "var_ords_time")

    return

    # # Try to find patterns in the two groups of variable orders
    # best_bool_comb_df = sorted_df[(sorted_df["Group_P_By_Edge_Order"].str.strip() == str.strip(sorted_df.iloc[0]["Group_P_By_Edge_Order"])) & (sorted_df["Generics_First"].str.strip() == str.strip(sorted_df.iloc[0]["Generics_First"])) ]
    # best_bool_comb_df["Order"] = best_bool_comb_df["Order"].str.replace(r"\(|\)|,|\'|\s","", regex=True).str.split('').str.join('')
    # best_size = best_bool_comb_df.iloc[0]["Size"]

    # best_perms = best_bool_comb_df[best_bool_comb_df["Size"] == best_size]
    # worst_perms = best_bool_comb_df[best_bool_comb_df["Size"] != best_size]

    # positions = {}

    # for p, perms in enumerate([best_perms, worst_perms]):
    #     for index, row in perms.iterrows():
    #         for i, c in enumerate([*row["Order"]]):
    #             if not c in positions:
    #                 positions[c] = []

    #             positions[c].append(i)

    #     avg_positions = {key: 0.0 for key in positions}
    #     for c in positions:
    #         avg_positions[c] = round(sum(positions[c]) / len(positions[c]),2)

    #     print(["Best", "Worst"][p], avg_positions)



    # mid = int((len(best_bool_comb_df) / 2))

    # best_bool_comb_df.reset_index(inplace=True, drop=True)
    # print_df = pd.concat([best_bool_comb_df.head(5), best_bool_comb_df.iloc[mid - 2: mid + 3], best_bool_comb_df.tail(5)])
    # print(print_df.head(15))


    # print(best_bool_comb_df[best_bool_comb_df["Order"] == "lvtsdep"[::-1]])

def times():
    results = pd.read_csv("../out/Reordering_csvs/results_more.csv", delimiter=";")
    results.to_pickle("../out/Reordering_csvs/results_more.pkl")
    df = pd.read_pickle("../out/Reordering_csvs/results_more.pkl")
    df.columns = [ "Group_P_By_Edge_Order", "Generics_First", "File","All_time", "NoClashTime", "FullNoClash"]
    
    df_full = pd.read_pickle("../out/Reordering_csvs/results.pkl")
    df_full.columns = ["File", "ID", "Group_P_By_Edge_Order", "Generics_First", "Order", "Mult_combined", "Size"]

    #df = pd.read_pickle("../out/Reordering_csvs/df_small.pkl")

    result_count_by_file = df_full.groupby(["File"], as_index=False).count()
    print(result_count_by_file.head(20))


    completed_files = result_count_by_file[result_count_by_file["ID"] == 322560]

    print(df.head())

    completed = df[df["File"].isin(completed_files["File"])]
    times = completed[["Group_P_By_Edge_Order", "Generics_First", "All_time"]].groupby(["Group_P_By_Edge_Order", "Generics_First"], as_index=False).mean()


    print(times.head(25))

if __name__ == "__main__":
    main()
    #times()
