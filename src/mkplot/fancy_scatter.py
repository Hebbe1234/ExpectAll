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
    return df.groupby([prows, pcols, 'seed', x_axis])[y_axis].median().reset_index()

def plot(grouped_df, prows, pcols, y_axis, x_axis, savedir):
    nrows, ncols = len(grouped_df.groupby(prows)),  len(grouped_df[pcols].unique())
    
    fig, axs = plt.subplots(nrows, ncols, squeeze=False, constrained_layout=True)
    for i, (value_of_parameter1, sub_df1) in enumerate(grouped_df.groupby(prows)):
        for j, (value_of_parameter2, sub_df2) in enumerate(sub_df1.groupby(pcols)):
            
           
                
            for seed, data in sub_df2.groupby('seed'):
                axs[i,j].scatter(data[x_axis], data[y_axis], label=f"Seed {seed}")
                axs[i,j].plot(data[x_axis], data[y_axis], color='black', label="_")

            axs[i,j].set_xlabel(x_axis)
            axs[i,j].set_ylabel(y_axis)
            axs[i,j].set_title(f"{prows}: {value_of_parameter1}, {pcols}: {value_of_parameter2}")
            # Set x-axis ticks to integer values
            axs[i,j].xaxis.set_major_locator(ticker.MaxNLocator(integer=True, min_n_ticks=1))
    
    save_dest = os.path.join("./fancy_scatter_plots", savedir)
    os.makedirs(save_dest, exist_ok=True)
    plt.savefig(os.path.join(save_dest,f"{prows}_{pcols}_{y_axis}_{x_axis}"), bbox_inches='tight', pad_inches=0.5) 
    plt.clf()

def main():
    parser = argparse.ArgumentParser("mainbdd.py")
    parser.add_argument("--data_dir", type=str, help="data_dir")
    parser.add_argument("--y_axis", default="solve_time", type=str, help="y-axis data")
    parser.add_argument("--x_axis", default="demands", type=str, help="x-axis data")
    parser.add_argument("--plot_rows", type=str, help="plot_rows")
    parser.add_argument("--plot_cols", type=str, help="plot_cols")
    parser.add_argument("--save_dir", default="scatter", type=str, help="dir to save to")
    args = parser.parse_args()

    df = read_json_files(args.data_dir)
    grouped_df = group_data(df, args.plot_rows, args.plot_cols,  args.y_axis, args.x_axis)
    plot(grouped_df, args.plot_rows, args.plot_cols, args.y_axis, args.x_axis, args.save_dir)

if __name__ == "__main__":
    main()
