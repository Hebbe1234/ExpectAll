import pandas as pd
import matplotlib.pyplot as mp
from itertools import permutations
import itertools

from itertools import chain, combinations
def all_subsets(ss):
    return chain(*map(lambda x: combinations(ss, x), range(0, len(ss)+1)))


if __name__ == "__main__":

    
    # results = pd.read_csv("../out/Reordering_csvs/results.csv", delimiter=";")
    # results.to_pickle("../out/Reordering_csvs/results.pkl")
    df = pd.read_pickle("../out/Reordering_csvs/results.pkl")
    df.columns = ["File", "ID", "Other_Order", "Generics_First", "Order", "Mult_combined", "Size"]


    result_count_by_file = df.groupby(["File"], as_index=False).count()
    print(result_count_by_file.shape)   
    print(result_count_by_file.head(100))   
     
     
    completed_files = result_count_by_file[result_count_by_file["ID"] == 241920]
    
    completed = df[df["File"].isin(completed_files["File"])]
    
    completed["Mult_combined"] = completed["Mult_combined"].str.replace(r"\(|\)|,|\'","", regex=True).str.split('').apply(sorted).str.join('')
    
    sizes = completed[["Other_Order", "Generics_First", "Order", "Size"]].groupby(["Other_Order", "Generics_First", "Order"], as_index=False).mean()
    sizes.reset_index(inplace=True, drop=True)
    
    
    sorted = sizes.sort_values(["Size"])
    sorted.reset_index(inplace=True, drop=True)
    # print(sorted.head(100000))

    print(len(sorted.iloc[0]["Generics_First"]), sorted.iloc[0]["Generics_First"].strip()  == "False ", len("False"))

    for b1 in [True, False]:
        for b2 in [True, False]:
            print(b1, b2)
            tt = sorted[(sorted["Other_Order"].str.strip() == str(b1)) & (sorted["Generics_First"].str.strip()  == str(b2)) ]
        
            print(tt.head())
            # ff.drop(columns=['index_0'])
            tt.reset_index(inplace=True, drop=True)
            tt.plot(y=["Size"], kind="line", figsize=(9, 8))
            mp.show()

    
    # print(sizes[(sizes["Order"] == sorted.iloc[0]["Order"]) &\
    #         (sizes["Mult_combined"] == sorted.iloc[0]["Mult_combined"]) &\
    #     #   (sizes["Mult_combined"] == sorted.iloc[0]["Mult_combined"]) &\
    #       (sizes["Other_Order"] == sorted.iloc[0]["Other_Order"]) &\
    #       (sizes["Generics_First"] == sorted.iloc[0]["Generics_First"])].head(1000))
    
    