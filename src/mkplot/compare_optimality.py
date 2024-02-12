import argparse
import os


def is_optimal(file_path, ):
    with open(file_path, "r") as file:
        lines = file.read().splitlines()

    #if  lines and "solve" in lines[-1]:
     #   solve_time = map(str.strip, lines[-1].split(":"))
    if not lines:
        return None
    
    lines = [l for l in lines if l]

    if "True" not in lines[-1] and "False" not in lines[-1]:
        return False
    
    wavelengths = len(["Has cudd" in l for l in lines])
    
    
    
# Extract running times for each graph for each demand
def compare_optimality(data_directory):
    is_optimal = 0
    for root, graph_dirs, _ in os.walk(data_directory):
        for graph_dir in graph_dirs:
            directory_path = os.path.join(root, graph_dir)
            for output in os.listdir(directory_path):
                pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser("cactus")
    parser.add_argument("--dirs", type=str, default=[],nargs="+",)
    parser.add_argument("--mip_dir", type=str,required=True)
    parser.add_argument("--select", type=int, default=[], nargs="+")
    args = parser.parse_args()

    dirs = args.dirs
    mip_dir = args.mip_dir
    select = args.select

    for dir in dirs:
        data_directory = f"../../out/{dir.split('__')[0]}" 
        compare_optimality(data_directory)