import argparse
import os


def is_optimal(file_path, mip_path, k):
    print(file_path)
    with open(file_path, "r") as file:
        lines = file.read().splitlines()

    print(mip_path)

    with open(mip_path, "r") as file:
        mip_lines = file.read().splitlines()

    # print(lines)
    
    if not lines:
        return False
    
    lines = [l for l in lines if l]

    if "True" not in lines[-1] and "False" not in lines[-1]:
        return False
    
    wavelengths = len([l for l in lines if "Has cudd" in  l])
    
    optimal_line = [l for l in mip_lines if "Optimal Wavelengths" in l]
    
    if len(optimal_line) == 0:
        return False
    
    mip_optimal = int(optimal_line[0].split(":")[1].split(".")[0])
    
    print(wavelengths, mip_optimal)
    return  wavelengths - k <= mip_optimal 
    
# Extract running times for each graph for each demand
def compare_optimality(data_directory, selected, mip_dir, mip_select, k):
    optimal_found = 0
    for root, graph_dirs, _ in os.walk(data_directory):
        for graph_dir in graph_dirs:
            directory_path = os.path.join(root, graph_dir)
            mip_directory_path = os.path.join(mip_dir, graph_dir)

            for output in os.listdir(directory_path):
                output_path = os.path.join(directory_path,output)
                
                mip_path = os.path.join(mip_directory_path,output)
                mip_path = mip_path.split("output")[0] + f"output{mip_select}.txt"
                number_of_demands = output.split("output")[1].split(".txt")[0]
                if not int(number_of_demands) == int(selected):
                    continue
                
                optimal_found += is_optimal(output_path, mip_path, k)

    print(optimal_found)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser("cactus")
    parser.add_argument("--dirs", type=str, default=[],nargs="+",)
    parser.add_argument("--mip_dir", type=str,required=True)
    parser.add_argument("--mip_select", type=int,default=15)
    parser.add_argument("--select", type=int, default=15)
    parser.add_argument("--k", type=int, default=0)
    args = parser.parse_args()

    dirs = args.dirs
    mip_dir = args.mip_dir
    select = args.select
    mip_select = args.mip_select

    for dir in dirs:
        data_directory = f"../../out/{dir.split('__')[0]}" 
        mip_directory = f"../../out/{mip_dir.split('__')[0]}" 
        compare_optimality(data_directory, select, mip_directory, mip_select, args.k)