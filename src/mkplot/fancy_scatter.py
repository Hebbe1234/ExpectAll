import os
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import matplotlib.ticker as ticker


def read_json_files(data_dir):
    dfs = []
    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            df = pd.read_json(os.path.join(data_dir, filename))
            dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

def group_data(df, prows, pcols, y_axis, x_axis, aggregation):   
    if aggregation == "median":
        return df.groupby([prows, pcols, 'seed', x_axis])[y_axis].median().reset_index()
    else:
        return df.groupby([prows, pcols, 'seed', x_axis])[y_axis].mean().reset_index()


def plot(grouped_df, prows, pcols, y_axis, x_axis, savedir, prefix=""):
    nrows, ncols = len(grouped_df.groupby(prows)),  len(grouped_df[pcols].unique())

    fig, axs = plt.subplots(nrows, ncols, squeeze=False, constrained_layout=True)
    for i, (value_of_parameter1, sub_df1) in enumerate(grouped_df.groupby(prows)):
        for j, (value_of_parameter2, sub_df2) in enumerate(sub_df1.groupby(pcols)):



            for seed, data in sub_df2.groupby('seed'):
                axs[i,j].scatter(data[x_axis], data[y_axis], label=f"Seed {seed}")
                axs[i,j].plot(data[x_axis], data[y_axis], color='black', label="_")

            axs[i,j].set_xlabel(x_axis)
            axs[i,j].set_ylabel(y_axis)
            title_row = f"{prows}: {value_of_parameter1}"
            title_col = f"{pcols}: {value_of_parameter2}"
                        
            axs[i,j].set_title(f"{title_row if prows != 'fake_row' else ''}{',' if prows != 'fake_row' and pcols != 'fake_col' else ''}{title_col if prows != 'fake_col' else ''}")
            
            # Set x-axis ticks to integer values
            axs[i,j].xaxis.set_major_locator(ticker.MaxNLocator(integer=True, min_n_ticks=1))

    save_dest = os.path.join("./fancy_scatter_plots", savedir)
    os.makedirs(save_dest, exist_ok=True)
    plt.savefig(os.path.join(save_dest,f"{prefix}{prows + '¤' if prows != 'fake_row' else ''}{pcols + '¤' if pcols != 'fake_col' else ''}¤{y_axis}¤{x_axis}"), bbox_inches='tight', pad_inches=0.5) 
    plt.clf()

def main():
    parser = argparse.ArgumentParser("mainbdd.py")
    parser.add_argument("--data_dir", type=str, help="data_dir")
    parser.add_argument("--y_axis", default="solve_time", type=str, help="y-axis data")
    parser.add_argument("--x_axis", default="demands", type=str, help="x-axis data")
    parser.add_argument("--plot_rows", default="fake_row", type=str, help="plot_rows")
    parser.add_argument("--plot_cols", default="fake_col", type=str, help="plot_cols")
    parser.add_argument("--save_dir", default="scatter", type=str, help="dir to save to")
    parser.add_argument("--aggregate", default="file", choices=["file", "median", "mean"], type=str, help="how to aggregate (or output combinations to files)")
    parser.add_argument('--change_values_file', nargs='+', help='A list of the values that should be used to generate file')

    args = parser.parse_args()

    df = read_json_files(args.data_dir)
    
    df["topology"] = df["filename"].replace("\\", "/").str.split("/").str[-1]
    
    df["fake_row"] = True
    df["fake_col"] = True
    
    if args.aggregate != "file":
        grouped_df = group_data(df, args.plot_rows, args.plot_cols,  args.y_axis, args.x_axis, args.aggregate)
        plot(grouped_df, args.plot_rows, args.plot_cols, args.y_axis, args.x_axis, args.save_dir)
    
    else:
        if args.change_values_file is None:
            raise Exception("You need to define the values, when trying to generate combination files")
        
        file_combination_df = df.drop([c for c in df.columns if c not in args.change_values_file], axis=1)
        df_unique = file_combination_df.drop_duplicates()

        print(df_unique.columns.tolist())
        
        unique_combinations = [tuple(row) for row in df_unique.to_numpy()]
        print(unique_combinations)
        
        for uc in unique_combinations:
            df_filtered = df.copy()
            
            mask = (df[file_combination_df.columns] == uc).all(axis=1)
            df_filtered = df[mask]
            
            prefix = ""
            for i,c in enumerate(df_unique.columns.tolist()):
                prefix += f"{c}={uc[i]}¤"
            
            grouped_df = group_data(df_filtered, args.plot_rows, args.plot_cols,  args.y_axis, args.x_axis, args.aggregate)
            plot(grouped_df, args.plot_rows, args.plot_cols, args.y_axis, args.x_axis, args.save_dir, prefix=prefix)
        
if __name__ == "__main__":
    main()
