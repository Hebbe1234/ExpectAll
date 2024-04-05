import argparse
import json
import pickle
import time
from RSABuilder import AllRightBuilder
from topology import get_gravity_demands, get_nx_graph, get_gravity_demands2_nodes_have_constant_size, get_demands_size_x
from demand_ordering import demand_order_sizes

from rsa_mip import SolveRSAUsingMIP
from niceBDD import ChannelData
rw = None
rsa = None
import json
import os

def output_result(args, bob: AllRightBuilder, all_time, res_output_file, bdd_output_file, replication_data_output_file_prefix):
    # Collect parsed arguments into a dictionary
    out_dict = {}
    for arg in vars(args):
        out_dict[arg] = getattr(args, arg)

    out_dict.update({
        "solved": bob.solved(),
        "size": bob.size(),
        "solve_time": bob.get_build_time(),
        "all_time": all_time,
    })

    # Write result dictionary to JSON file
    with open(res_output_file, 'w') as json_file:
        json.dump([out_dict], json_file, indent=4)
    
    # Write BDD to file
    bob.result_bdd.base.bdd.dump(bdd_output_file,  roots=[bob.result_bdd.expr])
    
    #Write replication data:
    with open(f'{replication_data_output_file_prefix}_channel_data.pickle', 'wb') as out_file:
        pickle.dump(bob.result_bdd.base.channel_data, out_file)
    
    with open(f'{replication_data_output_file_prefix}_demands.pickle', 'wb') as out_file:
        pickle.dump(bob.result_bdd.base.demand_vars, out_file)
    
    with open(f'{replication_data_output_file_prefix}_paths.pickle', 'wb') as out_file:
        pickle.dump(bob.result_bdd.base.paths, out_file)
    
    
    
    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser("mainbdd.py")
    parser.add_argument("--filename", type=str, help="file to run on")
    parser.add_argument("--result_output", default="../out/result.json", type=str, help="Where to output results")
    parser.add_argument("--bdd_output", default="../out/bdd.json", type=str, help="Where to output the bdd")
    parser.add_argument("--replication_output_file_prefix", default="../out", type=str, help="Where to output the data for replication")
    parser.add_argument("--seed", default=10, type=int, help="seed to use for random")
    parser.add_argument("--demands", default=10, type=int, help="number of demands")
    parser.add_argument("--experiment", default="baseline", type=str, help="baseline, increasing, wavelength_constraint, print_demands, wavelengths_static_demands, default_reordering, unary, sequence")
    parser.add_argument("--num_paths",default=1,  type=int, help="number of fixed paths per s/t combination")
    parser.add_argument("--path_type", default="DISJOINT", type=str, choices=["DISJOINT", "SHORTEST", "DEFAULT"], help="path type")
    
    
    parser.add_argument("--par1", type=str, help="extra param, cast to int if neccessary" )
    parser.add_argument("--par2", type=str, help="extra param, cast to int if neccessary" )
    parser.add_argument("--par3", type=str, help="extra param, cast to int if neccessary" )
    parser.add_argument("--par4", type=str, help="extra param, cast to int if neccessary" )
    parser.add_argument("--par5", type=str, help="extra param, cast to int if neccessary" )
    
    args = parser.parse_args()
    
    seed = args.seed    
    p1 = args.par1
    p2 = args.par2
    p3 = args.par3
    p4 = args.par4
    p5 = args.par5

    path_type = {
        "DEFAULT": AllRightBuilder.PathType.DEFAULT,    
        "SHORTEST": AllRightBuilder.PathType.SHORTEST,    
        "DISJOINT": AllRightBuilder.PathType.DISJOINT,    
    }[args.path_type]
    
    wavelengths = args.num_paths
    num_paths = args.num_paths

    G = get_nx_graph(args.filename)
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    demands = get_demands_size_x(G, args.demands)
    demands = demand_order_sizes(demands)
    
    print(demands)

    start_time_all = time.perf_counter()

    def save_to_json(data, folder, filename):
        # Create the folder if it doesn't exist
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        # Join folder and filename to get the complete path
        filepath = os.path.join(folder, filename)

        with open(filepath, 'w') as json_file:
            json.dump(data, json_file, indent=4)
            
    def save_to_txt(txt, folder, filename):
        # Create the folder if it doesn't exist
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        # Join folder and filename to get the complete path
        filepath = os.path.join(folder, filename)
        
        with open(filepath, 'w') as txt_file:
            txt_file.write(txt)
            
    if args.experiment == "exit": 
        exit()
    elif args.experiment == "mip_dt_old_things_shortest":
        from topology import get_disjoint_simple_paths, get_shortest_simple_paths
        bdd_paths = get_shortest_simple_paths(G, demands, 2) 
        max_slots = len(demands)
        channel_data = ChannelData(demands, max_slots)
        res = SolveRSAUsingMIP(G, demands,bdd_paths,channel_data.unique_channels, max_slots)
        save_to_json(res, args.experiment, str(len(demands)))
        save_to_txt(str(demands) + "\nSlotsUsed: " + str(max_slots), args.experiment,  str(len(demands))+".txt")

    elif args.experiment == "mip_kanto_old_things_shortest":
        from topology import get_disjoint_simple_paths, get_shortest_simple_paths
        bdd_paths = get_shortest_simple_paths(G, demands, 2) 
        max_slots = len(demands)
        channel_data = ChannelData(demands, max_slots)
        res = SolveRSAUsingMIP(G, demands,bdd_paths,channel_data.unique_channels, max_slots)
        save_to_json(res, args.experiment, str(len(demands)))
        save_to_txt(str(demands) + "\nSlotsUsed: " + str(max_slots), args.experiment,  str(len(demands))+".txt")

    elif args.experiment == "baseline":
        bob = AllRightBuilder(G, demands, wavelengths).construct()
    elif(args.experiment == "limited_v2"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().construct()         
    elif(args.experiment == "sequential_v2"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().sequential().construct()
    elif(args.experiment == "inc-par_v2"):
        bob = AllRightBuilder(G, demands, wavelengths).increasing().construct()
    elif(args.experiment == "inc-par_limited_v2"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().increasing().construct()
    elif(args.experiment == "inc-par_sequential_v2"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().sequential().increasing().construct()
    elif(args.experiment == "inc-par_limited_split_add_all_v2"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().increasing().split(True).construct()
    elif(args.experiment == "inc-par_limited_split_fancy_v2"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().increasing().split(False).construct()
    elif(args.experiment == "path_config_lim_1"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().path_configurations(1).path_type(path_type).construct()
    elif(args.experiment == "path_config_lim_10"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().path_configurations(10).path_type(path_type).construct()
    elif(args.experiment == "path_config_lim_50"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().path_configurations(50).path_type(path_type).construct()
    elif(args.experiment == "conf_lim_cliq_1"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().path_configurations(1).increasing(False).path_type(path_type).construct()
    elif(args.experiment == "conf_lim_cliq_10"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().path_configurations(10).increasing(True).clique().path_type(path_type).construct()
    elif(args.experiment == "conf_lim_cliq_50"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().path_configurations(50).increasing(True).clique().path_type(path_type).construct()
    elif (args.experiment == "clique_and_limited"):
        demands = get_gravity_demands2_nodes_have_constant_size(G, args.demands, seed=seed)
        demands = demand_order_sizes(demands)
        bob = AllRightBuilder(G, demands, num_paths).limited().path_type(path_type).clique().construct()   
    elif (args.experiment == "clique_limit_and_limited"):
        demands = get_gravity_demands2_nodes_have_constant_size(G, args.demands, seed=seed)
        demands = demand_order_sizes(demands)
        bob = AllRightBuilder(G, demands, num_paths).limited().path_type(path_type).clique(True).construct()
    elif (args.experiment == "single_path_limited_increasing"):
        demands = get_demands_size_x(G, args.demands, seed=seed, size=1)
        demands = demand_order_sizes(demands)
        print(demands)
        print("seed:", seed)
        bob = AllRightBuilder(G, demands, 1, slots=len(demands)).path_type(path_type).modulation({0:1}).limited().one_path().increasing(False).construct()
    elif (args.experiment == "single_path_limited_increasing_gravity_demands"):
        demands = get_gravity_demands2_nodes_have_constant_size(G, args.demands, seed=seed)
        demands = demand_order_sizes(demands)
        print(demands)
        
        bob = AllRightBuilder(G, demands, 1, 320).path_type(path_type).limited().one_path().increasing(False).construct()    
    elif (args.experiment == "sub_spectrum"):
        demands = get_gravity_demands2_nodes_have_constant_size(G, args.demands, seed=seed)
        bob = AllRightBuilder(G, demands, 1, slots=320).modulation({0:1}).limited().path_type(path_type).sub_spectrum(min(wavelengths, len(demands))).construct()
    else:
        raise Exception("Wrong experiment parameter", parser.print_help())

    end_time_all = time.perf_counter()

    all_time = end_time_all - start_time_all

    print("solve time; all time; satisfiable; size; solution_count; demands; wavelengths")
    print(f"{bob.get_build_time()};{all_time};{bob.solved()};{bob.size()};{-1};{args.demands};{wavelengths}")

    output_result(args, bob, all_time, args.result_output, args.bdd_output, args.replication_output_file_prefix)