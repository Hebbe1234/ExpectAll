import argparse
import json
import pickle
import time
from RSABuilder import AllRightBuilder
from channelGenerator import PathType, BucketType, MipType
from topology import get_channels, get_gravity_demands,get_gravity_demands_no_population, get_nx_graph, get_disjoint_simple_paths, get_overlapping_channels,get_safe_upperbound
from demand_ordering import demand_order_sizes
# from rsa_mip import SolveRSAUsingMIP
from niceBDD import ChannelData
rw = None
rsa = None
import json
import os
from fast_rsa_heuristic import fastHeuristic, calculate_usage, run_heuristic_n
from japan_mip_gurubi import SolveJapanMip, run_mip_n

os.environ["TMPDIR"] = "/scratch/rhebsg19/"

# start_time_constraint, end_time_constraint, solved, optimal_number,mip_parse_result = SolveRSAUsingMIP(G, demands, paths,channels, slots)

class MIPResult():
    def __init__(self, paths, demands, channels, start_time_constraint, end_time_constraint, solved, optimal_number,mip_parse_result, all_times=[]):
        self.solved = solved
        self.solve_time = time.perf_counter() - start_time_constraint
        self.constraint_time = end_time_constraint - start_time_constraint
        self.optimal_number = optimal_number
        self.mip_parse_result = mip_parse_result
        self.paths = paths
        self.demands = demands,
        self.channels = channels
        self.all_times = all_times
        
        
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
        "usage": mip_result.optimal_number,
        "all_times": mip_result.all_times
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
        pickle.dump(mip_result.mip_parse_result, out_file)

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
        "edge_evaluation": list(bob.edge_evaluation_score()) if bob.has_edge_evaluation() else [0,0,0,0,0,0,0],
        "k_link_resillience": list(bob.edge_evaluation_score())[6] if bob.has_edge_evaluation() else -1,
        "query_time": bob.query_time(),
        "gap_free_time": bob.get_sequential_time(),
        "count_least_changes" : bob.get_count_least_changes(),
        "time_points" : bob.get_time_points(),
        "usage_times": bob.get_usage_times(),
        "par_usage_times": bob.get_par_usage_times(),
        "optimize_time": bob.get_optimize_time(),
        "subtree_times": bob.get_subtree_query_times(),
        "failover_plus_build_time": bob.get_build_time() + bob.get_failover_build_time()
    })
    
    # Write result dictionary to JSON file
    with open(res_output_file, 'w') as json_file:
        json.dump([out_dict], json_file, indent=4)
    
    
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
    elif args.experiment in ['evaluate_k_link_resillience']:
        demands = get_gravity_demands_no_population(G, args.demands,multiplier=1, seed=seed)
    else:
        demands = get_gravity_demands(G, args.demands,multiplier=1, seed=seed)
    
    if "sub_spectrum" not in args.experiment:
        demands = demand_order_sizes(demands)
    
    slots = 320

    print(demands)
    mip_result = None
    
    bob = AllRightBuilder(G, demands, num_paths, slots=slots)

    start_time_all = time.perf_counter()
    if args.experiment == "is_safe_lim_safe_big":
        print("is_safe_lim_safe_big")
        num_of_demands = args.demands
        
        for seed in range(0, 20000):
            demands = get_gravity_demands(G,num_of_demands, seed=seed, max_uniform=30, multiplier=1)
            demands = demand_order_sizes(demands, True)
            p = AllRightBuilder(G, demands, 1, slots=320).dynamic_vars().safe_limited().set_heuristic_upper_bound().output_with_usage().construct()

            start_time_constraint, end_time_constraint, solved, optimal, demand_to_channels_res, _ = SolveJapanMip(G, demands, p.get_the_damn_paths(), 100)
        
            print(solved, p.solved())
            
            if optimal != p.usage() and solved:
                print(f"ERROR: MIP {optimal} vs BDD lim {p.usage()}")
                print("SEED: ", seed)
                break

    elif args.experiment == "is_safe_gapfree_new":
        print("is_safe_gapfree_new")
        num_of_demands = args.demands
        
        for seed in range(0, 20000):
            demands = get_gravity_demands(G,num_of_demands, seed=seed, max_uniform=30, multiplier=1)
            demands = demand_order_sizes(demands, True)
            p = AllRightBuilder(G, demands, 1, slots=320).dynamic_vars().sequential().set_heuristic_upper_bound().output_with_usage().construct()

            start_time_constraint, end_time_constraint, solved, optimal, demand_to_channels_res, _ = SolveJapanMip(G, demands, p.get_the_damn_paths(), p.get_the_damn_slots())
        
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
            p = AllRightBuilder(G, demands, 1, slots=320).dynamic_vars().safe_limited().set_heuristic_upper_bound().output_with_usage().construct()

            start_time_constraint, end_time_constraint, solved, optimal, demand_to_channels_res, _ = SolveJapanMip(G, demands, p.get_the_damn_paths(), 100)
        
            print(solved, p.solved())
            
            if optimal != p.usage() and solved:
                print(f"ERROR: MIP {optimal} vs BDD lim {p.usage()}")
                print("SEED: ", seed)
                break
    
    elif args.experiment == "mip_1":
        paths = get_disjoint_simple_paths(G, demands, num_paths)
        
        res, utilized = fastHeuristic(G, demands, paths, slots)
        usage = calculate_usage(utilized)
        
        start_time_constraint, end_time_constraint, solved,optimal_number, mip_parse_result, _ = SolveJapanMip(G, demands, paths, usage)
        mip_result = MIPResult(paths, demands, [], start_time_constraint, end_time_constraint, solved, optimal_number ,mip_parse_result)
    
    elif args.experiment == "mip_exhaustive":
        paths = get_disjoint_simple_paths(G, demands, num_paths)
        start_time_constraint, end_time_constraint, solved ,optimal_number, mip_parse_result, _ = SolveJapanMip(G, demands, paths, slots, MipType.EXHAUSTIVE)
        mip_result = MIPResult(paths, demands, [], start_time_constraint, end_time_constraint, solved, optimal_number,mip_parse_result)
    
    elif args.experiment == "mip_path_optimal":
        paths = get_disjoint_simple_paths(G, demands, num_paths)
        upper_bound = get_safe_upperbound(demands, paths, slots)
        start_time_constraint, end_time_constraint, solved ,optimal_number, mip_parse_result, _ = SolveJapanMip(G, demands, paths, upper_bound, MipType.PATHOPTIMAL)
        mip_result = MIPResult(paths, demands, [], start_time_constraint, end_time_constraint, solved, optimal_number,mip_parse_result)
    
    elif args.experiment == "mip_path_optimal_without_super_safe":
        paths = get_disjoint_simple_paths(G, demands, num_paths)
        start_time_constraint, end_time_constraint, solved ,optimal_number, mip_parse_result, _ = SolveJapanMip(G, demands, paths, slots, MipType.PATHOPTIMAL)
        mip_result = MIPResult(paths, demands, [], start_time_constraint, end_time_constraint, solved, optimal_number,mip_parse_result)
    
    elif args.experiment == "mip_safe":
        paths = get_disjoint_simple_paths(G, demands, num_paths)
        res, utilized = fastHeuristic(G, demands, paths, slots)
        usage = calculate_usage(utilized)
        _, _, _,optimal_number, _, _ = SolveJapanMip(G, demands, paths, usage)
        print(optimal_number,usage)

        start_time_constraint, end_time_constraint, solved ,optimal_number, mip_parse_result, _ = SolveJapanMip(G, demands, paths, optimal_number, MipType.SAFE)
        mip_result = MIPResult(paths, demands, [], start_time_constraint, end_time_constraint, solved, optimal_number,mip_parse_result)
    


    elif args.experiment == "mip_edge_failover_n":
        paths = get_disjoint_simple_paths(G, demands, num_paths)
        edge_failovers = int(p1)
        start_time_constraint = time.perf_counter()
        res_look_up,_ = run_mip_n(edge_failovers, G, demands, paths, slots, 10)
        mip_parse_result = res_look_up
        mip_result = MIPResult(paths, demands, [], start_time_constraint, time.perf_counter(), -1, -1,mip_parse_result)
    
    elif args.experiment == "heuristic_edge_failover_n":
        paths = get_disjoint_simple_paths(G, demands, num_paths)
        edge_failovers = int(p1)
        start_time_constraint = time.perf_counter()
        res_look_up = run_heuristic_n(edge_failovers, G, demands, paths, slots, 1000)
        mip_parse_result = res_look_up
        mip_result = MIPResult(paths, demands, [], start_time_constraint, time.perf_counter(), -1, -1,mip_parse_result)
    


    
    elif args.experiment == "fixed_size_demands":
        bob.construct()
    elif args.experiment == "fixed_size_demands_dynamic_vars":
        bob.dynamic_vars() .construct()
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
        mip_result = MIPResult(paths, demands, [], start_time_all, time.perf_counter(), utilized is not None, usage,res)

        
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


    elif args.experiment == "baseline":
        bob.dynamic_vars().output_with_usage().construct()
    elif args.experiment == "gap_free":
        bob.dynamic_vars().output_with_usage().sequential().construct()
    elif args.experiment == "increasing":
        bob.dynamic_vars().output_with_usage().increasing(True).construct()
    elif args.experiment == "super_safe_upperbound":
        bob.dynamic_vars().output_with_usage().set_super_safe_upper_bound().construct()

    elif args.experiment == "heuristic_upper_bound":
        bob.dynamic_vars().output_with_usage().set_heuristic_upper_bound().construct()
    elif args.experiment == "limited":
        bob.dynamic_vars().output_with_usage().limited().construct()
    elif args.experiment == "safe_limited":
        bob.dynamic_vars().output_with_usage().safe_limited().construct()
    elif args.experiment == "clique":
        bob.dynamic_vars().output_with_usage().clique().construct()
    elif args.experiment == "clique_internal_limit":
        bob.dynamic_vars().output_with_usage().clique(clique_limit=True).construct()
    elif args.experiment == "sub_spectrum":
        bob.dynamic_vars().output_with_usage().sub_spectrum(min(args.demands, int(p1)), BucketType.OVERLAPPING).construct()
     
    elif args.experiment == "gap_free_super_safe_upperbound":
        bob.dynamic_vars().output_with_usage().sequential().set_super_safe_upper_bound().construct()
    elif args.experiment == "gap_free_limited":
        bob.dynamic_vars().output_with_usage().sequential().limited().construct()
    elif args.experiment == "gap_free_safe_limited":
        bob.dynamic_vars().output_with_usage().sequential().safe_limited().construct()
        

    elif args.experiment == "failover_mip_n_query":
        failures = int(p1)
        num_queries = int(p2)
        paths = bob.get_the_damn_paths()
        start_time_constraint = time.perf_counter()
        
        failure_times = []
        mip_parse_result = {}

        for i in range(failures):
            lookup_res, all_times = run_mip_n(i+1, G, demands,paths, slots, num_queries)
            failure_times.append(all_times)
            mip_parse_result = lookup_res
            
        mip_result = MIPResult(paths, demands, [], start_time_constraint, time.perf_counter(), -1, -1,mip_parse_result, all_times=failure_times)

        


    elif args.experiment == "failover_dynamic_query":
        failures = int(p1)
        num_queries = int(p2)
        bob.safe_limited().sequential().dynamic_vars().set_super_safe_upper_bound().with_querying(failures,num_queries).construct()
    
    elif args.experiment == "failover_failover_query":
        failures = int(p1)
        num_queries = int(p2)
        bob.safe_limited().sequential().dynamic_vars().set_super_safe_upper_bound().failover(failures).with_querying(failures,num_queries).construct()
        
        
    elif args.experiment == "failover_dynamic_query_preserving":
        failures = int(p1)
        num_queries = int(p2)
        bob.safe_limited().sequential().dynamic_vars().set_super_safe_upper_bound().with_querying(failures,num_queries, 3600).construct()
    
    elif args.experiment == "failover_failover_query_preserving":
        failures = int(p1)
        num_queries = int(p2)
        bob.safe_limited().sequential().dynamic_vars().set_super_safe_upper_bound().failover(failures).with_querying(failures,num_queries, 3600).construct()
       
       
    elif args.experiment == "failover_dynamic_build":
        failures = int(p5) #Not needed. Just here for us to remember it
        bob.safe_limited().sequential().dynamic_vars().set_super_safe_upper_bound().construct()

    elif args.experiment == "failover_failover_build":
        failures = int(p5) #Not needed. Just here for us to remember it
        bob.safe_limited().sequential().dynamic_vars().set_super_safe_upper_bound().failover(failures).construct()


    elif args.experiment == "failover_dynamic_build_query":
        failures = int(p5) #Not needed. Just here for us to remember it
        bob.safe_limited().sequential().dynamic_vars().set_super_safe_upper_bound().with_querying(1,1).construct()

    elif args.experiment == "failover_failover_build_query":
        failures = int(p5) #Not needed. Just here for us to remember it
        bob.safe_limited().sequential().dynamic_vars().set_super_safe_upper_bound().failover(failures).with_querying(1,1).construct()


    elif args.experiment == "evaluate_k_link_resillience":
        bob.safe_limited().set_super_safe_upper_bound().use_edge_evaluation(int(p5)).construct()

    else:
        raise Exception("Wrong experiment parameter", parser.print_help())

    end_time_all = time.perf_counter()
    all_time = end_time_all - start_time_all

    print("solve time; all time; satisfiable; size; solution_count; demands; num_paths")
    if mip_result != None:
        print(f"{mip_result.solve_time};{all_time};{mip_result.solved};{1};{-1};{args.demands};{num_paths}")
        output_mip_result(args, mip_result, all_time,args.result_output, args.replication_output_file_prefix)
    else:
        bob.optimize()

        print(f"{bob.get_build_time()};{all_time};{bob.solved()};{bob.size()};{-1};{args.demands};{num_paths}")
        output_bdd_result(args, bob, all_time, args.result_output, args.bdd_output, args.replication_output_file_prefix)