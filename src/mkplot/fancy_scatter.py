import os
import numpy
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import matplotlib.ticker as ticker
import json
from matplotlib.pyplot import rcParams

# Changing font to stix; setting specialized math font properties as directly as possible
rcParams['mathtext.fontset'] = 'custom'
rcParams['mathtext.it'] = 'STIXGeneral:italic'
rcParams['mathtext.bf'] = 'STIXGeneral:italic:bold'

configuration = {
    "title": "",
    "x_unit": "",
    "y_unit":"",
    "experiment_mapping": {},
    "parameter_mapping": {},
    "file_name_pattern": "",
    "label_format": "#",
    "dpi": 100,
    "pad_y": 0.2,
    "pad_x": 0.25,
    "single_graph":False,
    "y_scale": 1,
    "legend_cols": 2,
    "y_log": False
    
}
uses_config = False

def read_json_files(data_dirs):
    dfs = []
    for data_dir in data_dirs:
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                df = pd.read_json(os.path.join(data_dir, filename))
                dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

def group_data(df, prows, pcols, y_axis, x_axis, bar_axis, aggregation, line_values):   
    if aggregation == "median":
        return df.groupby([prows, pcols, x_axis, "marker"] + line_values)[[y_axis, bar_axis]].median().reset_index()
    else:
        return df.groupby([prows, pcols, x_axis, "marker"] + line_values)[[y_axis, bar_axis]].mean().reset_index()


def report_transform(string: str):
    if not uses_config: 
        return string
    
    pm = configuration["parameter_mapping"]
    
    for p in pm:
        string = string.replace(p, pm[p])
    
    em = configuration["experiment_mapping"]
    
    for e in em:
        string = string.replace(e, em[e])
        
    return string.replace("_", " ").replace("(", "").replace(",)", "").replace(")", "").replace("'", "")

    
def plot(grouped_df, prows, pcols, y_axis, x_axis, bar_axis, line_values, savedir, prefix=""):
    nrows, ncols = len(grouped_df.groupby(prows)),  len(grouped_df[pcols].unique())

    fig, axs = plt.subplots(nrows, ncols, 
            squeeze=False, 
            # constrained_layout=True,
            figsize=(5*ncols, 5*nrows),
            )
    


    title = ",".join(prefix.split("¤"))
    if title[-1] == ",":
        title = title[0:-1]
        
    if uses_config:
        title = configuration["title"]       
    
    if title != "":
        fig.suptitle(title, fontsize=32)

    color_map = [ 'blue', 'red','green', 'brown', 'black', 'purple','khaki', 'lightgreen', 'pink', 'lightsalmon', 'lime',  'moccasin', 'olive', 'plum', 'peru', 'tan', 'tan2', 'khaki4', 'indigo']
    line_styles = ["--", "-.", ":"]
    
    lines = []
    
    
    ax2s = [[axs[r,c].twinx() if bar_axis != "fake_bar" else None for c in range(ncols)] for r in range(nrows)]
    
    line_styles = ["--", "-.", ":"]
  
    

    
    for i, (value_of_parameter1, sub_df1) in enumerate(grouped_df.groupby(prows)):
        for j, (value_of_parameter2, sub_df2) in enumerate(sub_df1.groupby(pcols)):
            for k,(seed, data) in enumerate(sub_df2.groupby(by=line_values)):

                seed = report_transform(str(seed))
                
                if not configuration["single_graph"]:
                    line = axs[i,j].scatter(data[x_axis].iloc[0], data[y_axis].iloc[0], label=configuration["label_format"].replace("#", seed), color=color_map[k], marker="o", linestyle=line_styles[k % len(line_styles)])
                
                
                if not configuration["single_graph"] and i == 0 and j == 0:
                    lines.append((line, configuration["label_format"].replace("#", seed)))
                
                
                width = 2
                if ax2s[i][j] is not None:
                    ax2s[i][j].bar(data[x_axis] + k*width, data[bar_axis], width, color=color_map[k], alpha=0.2)

                for f in range(len(data[x_axis])):

                    axs[i,j].plot(data[x_axis].iloc[f], data[y_axis].iloc[f], color=color_map[k % len(color_map)], linestyle=line_styles[k % len(line_styles)], marker=data["marker"].iloc[f])

                
                axs[i,j].plot(data[x_axis], data[y_axis], label=configuration["label_format"].replace("#", seed) if configuration["single_graph"] else "_", color=color_map[k % len(color_map)], linestyle=line_styles[k % len(line_styles)])

            
            if uses_config and configuration["y_log"]:
                axs[i,j].set_yscale("log")

            if uses_config:
                axs[i,j].set_xlabel(report_transform(x_axis) + (f" [{configuration['x_unit']}]" if configuration['x_unit'] != "" else ""), fontsize=16)
                axs[i,j].set_ylabel(report_transform(y_axis) + (f" [{configuration['y_unit']}]" if configuration['y_unit'] != "" else ""), fontsize=16)
            else:
                axs[i,j].set_xlabel(report_transform(x_axis), fontsize=16)
                axs[i,j].set_ylabel(report_transform(y_axis), fontsize=16)
            
            
            if ax2s[i][j] is not None:
                ax2s[i][j].set_ylabel(report_transform(bar_axis), fontsize=16)
           
            
            
            title_row = f"{report_transform(prows)}: {report_transform(str(value_of_parameter1))}"
            title_col = f"{report_transform(pcols)}: {report_transform(str(value_of_parameter2))}"
            
            
            axs[i,j].set_title(f"{title_row if prows != 'fake_row' else ''}{',' if prows != 'fake_row' and pcols != 'fake_col' else ''}{title_col if pcols != 'fake_col' else ''}", fontsize=16)
            # axs[i,j].legend(loc = 'upper left', ncol=1)
            # Set x-axis ticks to integer values
            axs[i,j].xaxis.set_major_locator(ticker.MaxNLocator(integer=True, min_n_ticks=1))


    
    
    # Hide both axes
    # set_lines = []
    # tracked_labels = []
    # for (l,g) in lines:
    #     if g not in tracked_labels:
    #         set_lines.append((l,g))
    #         # tracked_labels.append(g)
            
    # print(set_lines)
    # Adjust the layout to make room for the legend

    # plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
    
    if configuration["single_graph"]:
        axs[0,0].legend( loc = (-configuration["pad_x"], -configuration["pad_y"]), ncol=configuration["legend_cols"], labelspacing=0., fontsize=16)
    else:
        axs[0,0].legend([l for (l,g) in lines], [g for (l,g) in lines], loc = (-configuration["pad_x"], -configuration["pad_y"]), ncol=2, labelspacing=0., fontsize=16)

    save_dest = os.path.join("./fancy_scatter_plots", savedir)
    os.makedirs(save_dest, exist_ok=True)
    plt.savefig(
        os.path.join(save_dest,f"{prefix}{prows + '¤' if prows != 'fake_row' else ''}{pcols + '¤' if pcols != 'fake_col' else ''}¤{y_axis}¤{bar_axis + '¤' if bar_axis != 'fake_bar' else ''}{x_axis}"), bbox_inches='tight',
        # pad_inches=configuration["pad"],
        dpi=configuration["dpi"]
    ) 
    plt.clf()


def main():
    global uses_config
    global configuration
    
    parser = argparse.ArgumentParser("mainbdd.py")
    parser.add_argument("--data_dir", nargs='+', type=str, help="data_dir(s)")
    parser.add_argument("--config",  default = [], nargs='+', type=str, help="config")
    parser.add_argument("--y_axis", default="solve_time", type=str, help="y-axis data")
    parser.add_argument("--x_axis", default="demands", type=str, help="x-axis data")
    parser.add_argument("--bar", default="fake_bar", type=str, help="bar data")
    parser.add_argument("--line_values", default=["seed"], type=str, nargs='+', help="values for lines")
    parser.add_argument("--plot_rows", default="fake_row", type=str, help="plot_rows")
    parser.add_argument("--plot_cols", default="fake_col", type=str, help="plot_cols")
    parser.add_argument("--save_dir", default="scatter", type=str, help="dir to save to")
    parser.add_argument("--aggregate", default="file", choices=["file", "median", "mean"], type=str, help="how to aggregate (or output combinations to files)")
    parser.add_argument('--change_values_file', nargs='+', help='A list of the values that should be used to generate file')
    parser.add_argument('--solved_only', default="no", type=str,  help='Plot only solved?')
    parser.add_argument('--max_y', default=3600, type=int,  help='Max y value')
    parser.add_argument('--max_x', default=0, type=int,  help='Max x value')
    parser.add_argument('--filter_experiments', default=[], nargs='+',  help='Filter experiments')
    
    args = parser.parse_args()
    
    if args.config != []:
        uses_config = True
        for conf in args.config:
            with open(conf) as f:
                cf = json.loads(f.read())
                configuration.update(cf)
    
    df = read_json_files(args.data_dir)
    
    df["topology"] = df["filename"].replace("\\", "/").str.replace(".gml", "").str.split("/").str[-1]
    df["fake_row"] = True
    df["fake_col"] = True
    df["fake_bar"] = True
    
    df["marker"] = df["solved"].apply(lambda s: "." if s else "x")
    
    solved_only = str(args.solved_only).lower() in ["yes", "true"] 
    
    if len(args.filter_experiments) > 0:
        df = df[df["experiment"].isin(args.filter_experiments)]
    
    if solved_only:
        df = df[df["solved"] == True]
    
    
    df[args.y_axis] = df[args.y_axis].apply(lambda y: y * configuration["y_scale"])
    
    if args.max_x > 0:
        df = df[df[args.x_axis] < args.max_x]

    
    if args.max_y > 0:
        df = df[df[args.y_axis] < args.max_y]
    
    if args.aggregate != "file":
        grouped_df = group_data(df, args.plot_rows, args.plot_cols,  args.y_axis, args.x_axis, args.bar_axis, args.aggregate, args.line_values)
        plot(grouped_df, args.plot_rows, args.plot_cols, args.y_axis, args.x_axis, args.bar_axis, args.line_values, args.save_dir)
    
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
            
            grouped_df = group_data(df_filtered, args.plot_rows, args.plot_cols,  args.y_axis, args.x_axis, args.bar, args.aggregate, args.line_values)
            plot(grouped_df, args.plot_rows, args.plot_cols, args.y_axis, args.x_axis, args.bar,  args.line_values, args.save_dir, prefix=prefix)
        
if __name__ == "__main__":
    main()
