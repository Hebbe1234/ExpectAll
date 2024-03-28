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

def group_data(df, prows, pcols, y_axis, x_axis):
    df["topology"] = df["filename"].replace("\\", "/").str.split("/").str[-1]
    print(df)
    return df.groupby([prows, pcols, 'seed', x_axis])[y_axis].median().reset_index()

def plot(grouped_df, prows, pcols, y_axis, x_axis, savedir):
    nrows, ncols = len(grouped_df.groupby(prows)),  len(grouped_df[pcols].unique())
    
    fig, axs = plt.subplots(nrows, ncols, figsize=(18, 6))
    for i, (value_of_parameter1, sub_df1) in enumerate(grouped_df.groupby(prows)):
        for j, (value_of_parameter2, sub_df2) in enumerate(sub_df1.groupby(pcols)):
            
            if nrows > 1 and ncols > 1:
                ax = axs[i,j]
            elif nrows == 1 and ncols == 1:
                ax = axs
            elif nrows == 1:
                ax = axs[j]
            else:
                ax = axs[i]
                
            for seed, data in sub_df2.groupby('seed'):
                ax.scatter(data[x_axis], data[y_axis], label=f"Seed {seed}")
            
            ax.set_xlabel(x_axis)
            ax.set_ylabel(y_axis)
            ax.set_title(f"{prows}: {value_of_parameter1}, {pcols}: {value_of_parameter2}")
            ax.legend()
            # Set x-axis ticks to integer values
            ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, min_n_ticks=1))
    
    save_dest = os.path.join("./fancy_scatter_plots", savedir)
    os.makedirs(save_dest, exist_ok=True)
    plt.savefig(os.path.join(save_dest,f"{prows}_{pcols}"), bbox_inches = "tight")
    plt.clf()

def main():
    parser = argparse.ArgumentParser("mainbdd.py")
    parser.add_argument("--data_dir", type=str, help="data_dir")
    parser.add_argument("--y_axis", default="solve_time", type=str, help="y-axis data")
    parser.add_argument("--x_axis", default="demands", type=str, help="x-axis data")
    parser.add_argument("--plot_rows", type=str, help="plot_rows")
    parser.add_argument("--plot_cols", type=str, help="plot_cols")
    parser.add_argument("--savedir", default="scatter", type=str, help="dir to save to")
    args = parser.parse_args()

    df = read_json_files(args.data_dir)
    grouped_df = group_data(df, args.plot_rows, args.plot_cols,  args.y_axis, args.x_axis)
    plot(grouped_df, args.plot_rows, args.plot_cols, args.y_axis, args.x_axis, args.savedir)

if __name__ == "__main__":
    main()
