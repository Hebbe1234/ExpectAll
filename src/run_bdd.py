import argparse
import json
import pickle
import time
from RSABuilder import AllRightBuilder
from channelGenerator import PathType, BucketType
from topology import get_channels, get_gravity_demands, get_nx_graph, get_disjoint_simple_paths, get_overlapping_channels
from demand_ordering import demand_order_sizes
# from rsa_mip import SolveRSAUsingMIP
from niceBDD import ChannelData
rw = None
rsa = None
import json
import os
from fast_rsa_heuristic import fastHeuristic, calculate_usage
from japan_mip_gurubi import SolveJapanMip, run_mip_n


os.environ["TMPDIR"] = "/scratch/rhebsg19/"

# start_time_constraint, end_time_constraint, solved, optimal_number,mip_parse_result = SolveRSAUsingMIP(G, demands, paths,channels, slots)

class MIPResult():
    def __init__(self, paths, demands, channels, start_time_constraint, end_time_constraint, solved, optimal_number,mip_parse_result):
        self.solved = solved
        self.solve_time = time.perf_counter() - start_time_constraint
        self.constraint_time = end_time_constraint - start_time_constraint
        self.optimal_number = optimal_number
        self.mip_parse_result = mip_parse_result
        self.paths = paths
        self.demands = demands,
        self.channels = channels
        
        
def output_mip_result(args, mip_result: MIPResult, all_time, res_output_file, replication_data_output_file_prefix):
    # Collect parsed arguments into a dictionary
    out_dict = {}
    for arg in vars(args):
        out_dict[arg] = getattr(args, arg)
    
    out_dict.update({
        "solved": mip_result.solved,
        "size": 1,
        "solve_time": mip_result.solve_time,
        "all_time": all_time,
        "usage": mip_result.optimal_number
    })
    
    # Write result dictionary to JSON file
    with open(res_output_file, 'w') as json_file:
        json.dump([out_dict], json_file, indent=4)
    
    #Write replication data:
    with open(f'{replication_data_output_file_prefix}_channels.pickle', 'wb') as out_file:
        pickle.dump(mip_result.channels, out_file)
    
    with open(f'{replication_data_output_file_prefix}_demands.pickle', 'wb') as out_file:
        pickle.dump(mip_result.demands, out_file)
    
    with open(f'{replication_data_output_file_prefix}_paths.pickle', 'wb') as out_file:
        pickle.dump(mip_result.paths, out_file)
    
    with open(f'{replication_data_output_file_prefix}_mip_parse_result.pickle', 'wb') as out_file:
        pickle.dump(mip_parse_result, out_file)

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
        "usage": bob.usage(),
        "edge_evaluation": list(bob.edge_evaluation_score())
    })

    # Write result dictionary to JSON file
    with open(res_output_file, 'w') as json_file:
        json.dump([out_dict], json_file, indent=4)
    
    # # Write BDD to file
    # bob.result_bdd.base.bdd.dump(bdd_output_file,  roots=[bob.result_bdd.expr])
    # # Special for sub spectrum as we also must save the individual sub spectrum BDD's
    # if bob.is_sub_spectrum():
    #     for i, (rs, index, base) in enumerate(bob.get_sub_spectrum_blocks()):
    #         base.bdd.dump(bdd_output_file.replace(".json", f"_{i}.json"),  roots=[rs.expr])
    #         with open(f'{replication_data_output_file_prefix}_{i}_start_index.json', 'w') as out_file:
    #             json.dump({"start_index":index}, out_file, indent=4)
                
    #         with open(f'{replication_data_output_file_prefix}_{i}_base.pickle', 'wb') as out_file:
    #             base.bdd = None
    #             pickle.dump(base, out_file)

    # #Write replication data:
    # with open(f'{replication_data_output_file_prefix}_channel_data.pickle', 'wb') as out_file:
    #     pickle.dump(bob.result_bdd.base.channel_data, out_file)
    
    # with open(f'{replication_data_output_file_prefix}_demands.pickle', 'wb') as out_file:
    #     pickle.dump(bob.result_bdd.base.demand_vars, out_file)
    
    # with open(f'{replication_data_output_file_prefix}_paths.pickle', 'wb') as out_file:
    #     pickle.dump(bob.result_bdd.base.paths, out_file)
    
    # with open(f'{replication_data_output_file_prefix}_expr.pickle', 'wb') as out_file:
    #     pickle.dump(bob.result_bdd.expr, out_file)
    
    # with open(f'{replication_data_output_file_prefix}_base.pickle', 'wb') as out_file:
    #     bob.result_bdd.base.bdd = None
    #     pickle.dump(bob.result_bdd.base, out_file)
    
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

    num_paths = args.num_paths
    
    G = get_nx_graph(args.filename)
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")


    if args.experiment in ['fixed_size_demands', 'fixed_size_demands_usage', 'unsafe_rounded_channels']:
        demands = get_gravity_demands(G, args.demands,multiplier=int(p1), seed=seed)
    else:
        demands = get_gravity_demands(G, args.demands,multiplier=1, seed=seed)
    
    if "sub_spectrum" not in args.experiment:
        demands = demand_order_sizes(demands)
    
    slots = 320

    print(demands)
    mip_result = None
    
    bob = AllRightBuilder(G, demands, num_paths, slots=slots)

    start_time_all = time.perf_counter()
    if args.experiment == "baseline":
        bob.construct()
        
    elif args.experiment == "baseline_demand_path":
        bob.use_demand_path().construct()
    
    elif args.experiment == "lim":
        bob.limited().construct()
    
    elif args.experiment == "safe_lim":
        bob.safe_limited().construct()
    
    elif args.experiment == "seq":
        bob.sequential().construct()
    
    elif args.experiment == "lim_seq":
        bob.sequential().limited().construct()
    
    elif args.experiment == "safe_lim_seq":
        bob.safe_limited().sequential().construct()
    
    elif args.experiment == "lim_inc":
        bob.limited().optimal().construct() #Optimal simulates increasing
    
    elif args.experiment == "seq_inc":
        bob.sequential().optimal().construct() #Optimal simulates increasing
    
    elif args.experiment == "baseline_dynamic_vars":
        bob.dynamic_vars().construct()
        
    elif args.experiment == "dynamic_vars_seq":
        bob.dynamic_vars().sequential().construct()
    
    elif args.experiment == "dynamic_vars_lim":
        bob.dynamic_vars().limited().construct()
    
    elif args.experiment == "dynamic_vars_safe_lim":
        bob.safe_limited().dynamic_vars().construct()
    
    elif args.experiment == "dynamic_vars_lim_seq":
        bob.dynamic_vars().sequential().limited().construct()
    
    elif args.experiment == "dynamic_vars_safe_lim_seq":
        bob.safe_limited().dynamic_vars().sequential().construct()
    
    elif args.experiment == "is_safe_lim_safe_big":
        print("is_safe_lim_safe_big")
        num_of_demands = args.demands
        
        for seed in range(0, 20000):
            demands = get_gravity_demands(G,num_of_demands, seed=seed, max_uniform=30, multiplier=1)
            demands = demand_order_sizes(demands, True)
            p = AllRightBuilder(G, demands, 1, slots=320).dynamic_vars().safe_limited().set_upper_bound().output_with_usage().construct()

            start_time_constraint, end_time_constraint, solved, optimal, demand_to_channels_res, _ = SolveJapanMip(G, demands, p.get_the_damn_paths(), 100)
        
            print(solved, p.solved())
            
            if optimal != p.usage() and solved:
                print(f"ERROR: MIP {optimal} vs BDD lim {p.usage()}")
                print("SEED: ", seed)
                break
    
    elif args.experiment == "is_safe_lim_safe_small":
        print("is_safe_lim_safe_small")
        num_of_demands = args.demands
        
        for seed in range(0, 20000):
            demands = get_gravity_demands(G,num_of_demands, seed=seed, max_uniform=30, multiplier=1)
            demands = demand_order_sizes(demands, False)
            p = AllRightBuilder(G, demands, 1, slots=320).dynamic_vars().safe_limited().set_upper_bound().output_with_usage().construct()

            start_time_constraint, end_time_constraint, solved, optimal, demand_to_channels_res, _ = SolveJapanMip(G, demands, p.get_the_damn_paths(), 100)
        
            print(solved, p.solved())
            
            if optimal != p.usage() and solved:
                print(f"ERROR: MIP {optimal} vs BDD lim {p.usage()}")
                print("SEED: ", seed)
                break
    
    elif args.experiment == "mip_1":
        paths = get_disjoint_simple_paths(G, demands, num_paths)
        start_time_constraint, end_time_constraint, solved,optimal_number, mip_parse_result, _ = SolveJapanMip(G, demands, paths, slots)
        mip_result = MIPResult(paths, demands, [], start_time_constraint, end_time_constraint, solved, optimal_number ,mip_parse_result)
    
    elif args.experiment == "mip_all":
        paths = get_disjoint_simple_paths(G, demands, num_paths)
        start_time_constraint, end_time_constraint, solved ,optimal_number, mip_parse_result, _ = SolveJapanMip(G, demands, paths, slots, True)
        mip_result = MIPResult(paths, demands, [], start_time_constraint, end_time_constraint, solved, optimal_number,mip_parse_result)
    
    elif args.experiment == "mip_edge_failover_n":
        paths = get_disjoint_simple_paths(G, demands, num_paths)
        edge_failovers = int(p1)
        start_time_constraint = time.perf_counter()
        res_look_up = run_mip_n(edge_failovers, G, demands, paths, slots)
        mip_parse_result = res_look_up
        mip_result = MIPResult(paths, demands, [], -1, -1, -1, -1,mip_parse_result)
    

    elif args.experiment == "sub_spectrum":
        bob.limited().sub_spectrum(min(args.demands, int(p1))).construct()
        
    elif args.experiment == "fixed_size_demands":
        bob.construct()
    elif args.experiment == "fixed_size_demands_dynamic_vars":
        bob.dynamic_vars().construct()
    elif args.experiment == "fixed_channels":
        if int(p2) == 0:
            bob.fixed_channels(int(p1), num_paths, f"mip_{p1}_{args.filename.split('/')[-1]}", load_cache=False).construct()
        else:
            bob.dynamic_vars().fixed_channels(int(p1), num_paths, f"mip_{p1}_{args.filename.split('/')[-1]}", load_cache=False).construct()
    elif args.experiment == "fast_heuristic": 
        demands = demand_order_sizes(demands, True)
        paths = get_disjoint_simple_paths(G, demands, num_paths)

        res, utilized = fastHeuristic(G, demands, paths, slots)
        usage = calculate_usage(utilized)
    elif args.experiment == "fixed_channels_heuristics":
        bob.dynamic_vars().fixed_channels(int(p1), num_paths, f"mip_{p1}_{args.filename.split('/')[-1]}", load_cache=False).construct()
    elif args.experiment == "baseline_lim_inc_usage":
        bob.dynamic_vars().limited().increasing().output_with_usage().construct() 
    elif args.experiment == "sub_spectrum_usage":
        k = int(p1)
        bob.limited().sub_spectrum(min(args.demands, k)).output_with_usage().construct()
    elif args.experiment == "fixed_size_demands_usage":
        bob.dynamic_vars().limited().output_with_usage().construct()
    elif args.experiment == "fixed_channels_heuristics_usage":
        bob.dynamic_vars().fixed_channels(num_paths, num_paths, f"mip_{p1}_{args.filename.split('/')[-1]}", load_cache=False).output_with_usage().construct()


    elif args.experiment == "safe_baseline":
        bob.dynamic_vars().construct()
    elif args.experiment == "safe_baseline_inc":
        bob.dynamic_vars().increasing().construct()
    elif args.experiment == "safe_baseline_gap_free":
        bob.dynamic_vars().sequential().construct()
    elif args.experiment == "safe_baseline_upper_bound":
        bob.dynamic_vars().set_upper_bound().construct()

    elif args.experiment == "unsafe_limited":
        bob.dynamic_vars().set_upper_bound().output_with_usage().limited().construct()
    elif args.experiment == "unsafe_safe_limited":
        bob.dynamic_vars().set_upper_bound().output_with_usage().safe_limited().construct()
    elif args.experiment == "unsafe_fixed_channels_k":
        bob.dynamic_vars().set_upper_bound().output_with_usage().fixed_channels(channels_per_demand=int(p1)).construct()
    elif args.experiment == "unsafe_rounded_channels":
        bob.dynamic_vars().set_upper_bound().output_with_usage().construct()
    elif args.experiment == "unsafe_sub_spectrum":
        bob.dynamic_vars().set_upper_bound().output_with_usage().sub_spectrum(min(args.demands, int(p1)), BucketType.OVERLAPPING)
    else:
        raise Exception("Wrong experiment parameter", parser.print_help())

    end_time_all = time.perf_counter()

    all_time = end_time_all - start_time_all

    print("solve time; all time; satisfiable; size; solution_count; demands; num_paths")
    if mip_result != None:
        print(f"{mip_result.solve_time};{all_time};{mip_result.solved};{1};{-1};{args.demands};{num_paths}")
        output_mip_result(args, mip_result, all_time,args.result_output, args.replication_output_file_prefix)
    else:
        print(f"{bob.get_build_time()};{all_time};{bob.solved()};{bob.size()};{-1};{args.demands};{num_paths}")
        output_bdd_result(args, bob, all_time, args.result_output, args.bdd_output, args.replication_output_file_prefix)