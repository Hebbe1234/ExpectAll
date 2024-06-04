import argparse
import json
import time
from RSABuilder import AllRightBuilder
from topology import get_gravity_demands,get_gravity_demands_no_population, get_nx_graph, get_disjoint_simple_paths
from demand_ordering import demand_order_sizes
rw = None
rsa = None
import json
import os
from fast_rsa_heuristic import fastHeuristic, calculate_usage
from japan_mip_gurubi import SolveJapanMip, run_mip_n

os.environ["TMPDIR"] = "/scratch/rhebsg19/"


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
        
        
def output_mip_result(args, mip_result: MIPResult, all_time, res_output_file):
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


def output_bdd_result(args, bob: AllRightBuilder, all_time, res_output_file):
    # Collect parsed arguments into a dictionary
    out_dict = {}
    for arg in vars(args):
        out_dict[arg] = getattr(args, arg)

    no_change_query_times, no_change_query_solved_times, no_change_query_infeasible_counts, no_change_query_solved_counts, no_change_query_not_solved_but_feasible_counts, query_impossible_count = bob.get_no_change_info()
 

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
        "time_points" : bob.get_time_points(),
        "usage_times": bob.get_usage_times(),
        "optimize_time": bob.get_optimize_time(),
        "subtree_times": bob.get_subtree_query_times(),
        "failover_plus_build_time": bob.get_build_time() + bob.get_failover_build_time(),
        "no_change_query_times": no_change_query_times,
        "no_change_query_solved_times": no_change_query_solved_times,
        "no_change_query_infeasible_counts": no_change_query_infeasible_counts,
        "no_change_query_solved_counts": no_change_query_solved_counts,
        "no_change_query_not_solved_but_feasible_counts": no_change_query_not_solved_but_feasible_counts,
        "query_impossible_count": query_impossible_count
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
    elif args.experiment in ['evaluate_k_link_resillience', "clique_resilience"]:
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
    
    
    if args.experiment == "mip_1":
        paths = get_disjoint_simple_paths(G, demands, num_paths)
        
        res, utilized = fastHeuristic(G, demands, paths, slots)
        usage = calculate_usage(utilized)
        
        start_time_constraint, end_time_constraint, solved,optimal_number, mip_parse_result, _ = SolveJapanMip(G, demands, paths, usage)
        mip_result = MIPResult(paths, demands, [], start_time_constraint, end_time_constraint, solved, optimal_number ,mip_parse_result)
  

    elif args.experiment == "mip_edge_failover_n":
        paths = get_disjoint_simple_paths(G, demands, num_paths)
        edge_failovers = int(p1)
        start_time_constraint = time.perf_counter()
        res_look_up,_ = run_mip_n(edge_failovers, G, demands, paths, slots, 10)
        mip_parse_result = res_look_up
        mip_result = MIPResult(paths, demands, [], start_time_constraint, time.perf_counter(), -1, -1,mip_parse_result)
        

    elif args.experiment == "failover_mip_n_query":
        failures = int(p1)
        num_queries = int(p2)
        paths = bob.get_paths()
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
        bob.safe_limited().sequential().set_super_safe_upper_bound().with_querying(failures,num_queries).construct()
    
    elif args.experiment == "failover_failover_query":
        failures = int(p1)
        num_queries = int(p2)
        bob.safe_limited().sequential().set_super_safe_upper_bound().failover(failures).with_querying(failures,num_queries).construct()
        
        
    elif args.experiment == "failover_dynamic_query_preserving":
        failures = int(p1)
        num_queries = int(p2)
        bob.safe_limited().sequential().set_super_safe_upper_bound().with_querying(failures,num_queries, 3600).construct()
    
    elif args.experiment == "failover_failover_query_preserving":
        failures = int(p1)
        num_queries = int(p2)
        bob.safe_limited().sequential().set_super_safe_upper_bound().failover(failures).with_querying(failures,num_queries, 3600).construct()
       

    elif args.experiment == "failover_dynamic_build_query":
        failures = int(p5) #Not needed. Just here for us to remember it
        bob.safe_limited().sequential().set_super_safe_upper_bound().with_querying(1,1).construct()

    elif args.experiment == "failover_failover_build_query":
        failures = int(p5) #Not needed. Just here for us to remember it
        bob.safe_limited().sequential().set_super_safe_upper_bound().failover(failures).with_querying(1,1).construct()


    elif args.experiment == "evaluate_k_link_resillience":
        bob.safe_limited().set_super_safe_upper_bound().use_edge_evaluation(int(p5)).construct()

    elif args.experiment == "clique_resilience":
        bob.clique(clique_limit=True).use_edge_evaluation(int(p5)).construct()
        

    else:
        raise Exception("Wrong experiment parameter", parser.print_help())

    end_time_all = time.perf_counter()
    all_time = end_time_all - start_time_all

    print("solve time; all time; satisfiable; size; solution_count; demands; num_paths")
    if mip_result != None:
        print(f"{mip_result.solve_time};{all_time};{mip_result.solved};{1};{-1};{args.demands};{num_paths}")
        output_mip_result(args, mip_result, all_time,args.result_output)
    else:
        bob.optimize()

        print(f"{bob.get_build_time()};{all_time};{bob.solved()};{bob.size()};{-1};{args.demands};{num_paths}")
        output_bdd_result(args, bob, all_time, args.result_output)