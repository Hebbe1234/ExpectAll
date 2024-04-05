import argparse
import json
import pickle
import time
from RSABuilder import AllRightBuilder
from topology import get_channels, get_gravity_demands, get_nx_graph, get_disjoint_simple_paths, get_overlapping_channels
from demand_ordering import demand_order_sizes
from rsa_mip import SolveRSAUsingMIP
from niceBDD import ChannelData
rw = None
rsa = None
import json
import os

def output_bdd_result(args, bob: AllRightBuilder, all_time, res_output_file, bdd_output_file, replication_data_output_file_prefix):
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
    
    # Special for sub spectrum as we also must save the individual sub spectrum BDD's
    if bob.__sub_spectrum:
        for i, (rs, index) in enumerate(bob.__sub_spectrum_blocks):
            bob.result_bdd.base.bdd.dump(bdd_output_file.replace(".json", f"_{i}.json"),  roots=[rs.expr])
            with open(f'{replication_data_output_file_prefix}_{i}_start_index.json', 'w') as out_file:
                json.dump({"start_index":index}, out_file, indent=4)

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

    demands = get_gravity_demands(G, args.demands)
    demands = demand_order_sizes(demands)
    
    slots = 320

    print(demands)

    bob = AllRightBuilder(G, demands, num_paths, slots=slots)

    start_time_all = time.perf_counter()
    if args.experiment == "baseline":
        bob.construct()
    if args.experiment == "lim_inc":
        bob.limited().optimal().construct() #Optimal simulates increasing
    if args.experiment == "seq_inc":
        bob.sequential().optimal().construct() #Optimal simulates increasing
    if args.experiment == "mip 1":
        paths = get_disjoint_simple_paths(G, demands, 1)
        demand_channels = get_channels(demands, slots, limit=False)
        _, channels = get_overlapping_channels(demand_channels)
        start_time_constraint, end_time_constraint, solved, optimal_number,_ = SolveRSAUsingMIP(G, demands, paths,channels, slots)
    else:
        raise Exception("Wrong experiment parameter", parser.print_help())


    end_time_all = time.perf_counter()

    all_time = end_time_all - start_time_all

    print("solve time; all time; satisfiable; size; solution_count; demands; wavelengths")
    print(f"{bob.get_build_time()};{all_time};{bob.solved()};{bob.size()};{-1};{args.demands};{wavelengths}")

    
    output_bdd_result(args, bob, all_time, args.result_output, args.bdd_output, args.replication_output_file_prefix)
