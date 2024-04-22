
import pandas as pd
import os

def read_json_files(data_dirs):
    dfs = []
    for data_dir in data_dirs:
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                df = pd.read_json(os.path.join(data_dir, filename))
                df['id'] = filename.split('.')[0]
                dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


if __name__ == "__main__":
    df = read_json_files(['../../out/EXPERIMENT_1_1_RUN_2/results', '../../out/EXPERIMENT_0_9_RUN_1/results'])
    df = df[(df['seed'] == 2) & (df['filename'] == "../src/topologies/japanese_topologies/kanto11.gml") & (df['num_paths'] == 2)]
    df = df[df['demands'] == 9]
    
    df.to_csv('./search.csv')
