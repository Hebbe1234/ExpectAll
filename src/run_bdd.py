import argparse
import time
from RSABuilder import AllRightBuilder
from topology import get_gravity_demands, get_nx_graph, get_gravity_demands2_nodes_have_constant_size, get_demands_size_x
from demand_ordering import demand_order_sizes

rw = None
rsa = None


def print_demands(filename, demands, wavelengths):
    print("graph: ", filename, "wavelengths: ", wavelengths, "demands: ")
    print(demands)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("mainbdd.py")
    parser.add_argument("--filename", type=str, help="file to run on")
    parser.add_argument("--wavelengths", default=10, type=int, help="number of wavelengths")
    parser.add_argument("--demands", default=10, type=int, help="number of demands")
    parser.add_argument("--experiment", default="baseline", type=str, help="baseline, increasing, wavelength_constraint, print_demands, wavelengths_static_demands, default_reordering, unary, sequence")
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

    wavelengths = args.wavelengths
    num_paths = args.wavelengths

    G = get_nx_graph(args.filename)
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    demands = get_gravity_demands2_nodes_have_constant_size(G, args.demands)
    demands = demand_order_sizes(demands)
    
    solved = False
    size = 0
    solve_time = 0

    print(demands)
    
    start_time_all = time.perf_counter()
    
    if args.experiment == "exit": 
        exit()
    elif args.experiment == "baseline_v2":
        bob = AllRightBuilder(G, demands, wavelengths).construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())
    elif(args.experiment == "limited_v2"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())     
    elif(args.experiment == "sequential_v2"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().sequential().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())     
    elif(args.experiment == "inc-par_v2"):
        bob = AllRightBuilder(G, demands, wavelengths).increasing().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())     
    elif(args.experiment == "inc-par_limited_v2"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().increasing().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())   
    elif(args.experiment == "inc-par_sequential_v2"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().sequential().increasing().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())   
    elif(args.experiment == "inc-par_limited_split_add_all_v2"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().increasing().split(True).construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())   
    elif(args.experiment == "inc-par_limited_split_fancy_v2"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().increasing().split(False).construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())   

    elif(args.experiment == "path_config_lim_1"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().path_configurations(1).path_type(AllRightBuilder.PathType.DISJOINT).construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())  
    elif(args.experiment == "path_config_lim_10"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().path_configurations(10).path_type(AllRightBuilder.PathType.DISJOINT).construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())  
    elif(args.experiment == "path_config_lim_50"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().path_configurations(50).path_type(AllRightBuilder.PathType.DISJOINT).construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())  
    elif(args.experiment == "conf_lim_cliq_1"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().path_configurations(1).increasing(False).path_type(AllRightBuilder.PathType.DISJOINT).construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())  
    elif(args.experiment == "conf_lim_cliq_10"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().path_configurations(10).increasing(True).clique().path_type(AllRightBuilder.PathType.DISJOINT).construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())  
    elif(args.experiment == "conf_lim_cliq_50"):
        bob = AllRightBuilder(G, demands, wavelengths).limited().path_configurations(50).increasing(True).clique().path_type(AllRightBuilder.PathType.DISJOINT).construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())
    
    elif (args.experiment == "clique_and_limited"):
        seed = int(p1) if p1 is not None else 10
        demands = get_gravity_demands2_nodes_have_constant_size(G, args.demands, seed=seed)
        demands = demand_order_sizes(demands)
        bob = AllRightBuilder(G, demands, num_paths).limited().path_type(path_type=AllRightBuilder.PathType.SHORTEST).clique().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())  
    elif (args.experiment == "clique_limit_and_limited"):
        seed = int(p1) if p1 is not None else 10
        demands = get_gravity_demands2_nodes_have_constant_size(G, args.demands, seed=seed, size=1)
        demands = demand_order_sizes(demands)
        bob = AllRightBuilder(G, demands, num_paths).limited().path_type(path_type=AllRightBuilder.PathType.SHORTEST).clique(True).construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())  
        
    elif (args.experiment == "single_path_limited_increasing"):
        p1 = int(p1) if p1 is not None else 10
        demands = get_demands_size_x(G, args.demands, seed=p1, size=1)
        demands = demand_order_sizes(demands)
        print(demands)
        print("seed:", p1)
        bob = AllRightBuilder(G, demands, 1, slots=len(demands)).path_type(path_type=AllRightBuilder.PathType.SHORTEST).modulation({0:1}).limited().one_path().increasing(False).construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())
    elif (args.experiment == "single_path_limited_increasing_gravity_demands"):
        p1 = int(p1) if p1 is not None else 10
        demands = get_gravity_demands2_nodes_have_constant_size(G, args.demands, seed=p1)
        demands = demand_order_sizes(demands)
        print(demands)
        
        bob = AllRightBuilder(G, demands, 1, 320).path_type(path_type=AllRightBuilder.PathType.SHORTEST).limited().one_path().increasing(False).construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())
        
    
    elif (args.experiment == "sub_spectrum"):
        demands = get_gravity_demands2_nodes_have_constant_size(G, args.demands)
        bob = AllRightBuilder(G, demands, 1, slots=320).modulation({0:1}).limited().path_type(AllRightBuilder.PathType.SHORTEST).sub_spectrum(min(wavelengths, len(demands))).construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())  

    # if args.experiment == "baseline":
    #     bob = AllRightBuilder(G, demands, wavelengths).construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())
    # elif(args.experiment == "encoded_paths_increasing_parallel_sequential"):
    #     bob = AllRightBuilder(G, demands, 8).encoded_fixed_paths(wavelengths).increasing().sequential().construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())         
    # elif args.experiment == "encoded_disjoint_fixed_paths_inc_par_sec":
    #     bob = AllRightBuilder(G, demands, 8).encoded_fixed_paths(args.wavelength, AllRightBuilder.PathType.DISJOINT).increasing().sequential().construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())  
    # elif args.experiment == "encoded_fixed_paths_inc_par_seq_cliq":
    #     bob = AllRightBuilder(G, demands, 8).encoded_fixed_paths(wavelengths).increasing().sequential().clique().construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())  
    # elif args.experiment == "encoded_3_fixed_paths_inc_par_seq":
    #     bob = AllRightBuilder(G, demands, wavelengths).encoded_fixed_paths(3).increasing().sequential().construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())      
    # elif args.experiment == "encoded_3_fixed_paths_inc_par_seq_clique":
    #     bob = AllRightBuilder(G, demands, wavelengths).encoded_fixed_paths(3).increasing().sequential().clique().construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())  
    # elif args.experiment == "increasing_parallel_sequential_reordering":
    #     bob = AllRightBuilder(G, demands, wavelengths).increasing().sequential().construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())        
    # elif args.experiment == "increasing_parallel_dynamic_limited":
    #     bob = AllRightBuilder(G, demands, wavelengths).increasing().dynamic().limited().construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    # elif args.experiment == "dynamic_limited":
    #     bob = AllRightBuilder(G, demands, wavelengths).dynamic().limited().construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    # elif args.experiment == "wavelength_constraint":
    #     bob = AllRightBuilder(G, demands, wavelengths).limited().construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    # elif args.experiment == "naive_fixed_paths":
    #     bob = AllRightBuilder(G, demands, 8).naive_fixed_paths(wavelengths).construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    # elif args.experiment == "encoded_fixed_paths":
    #     bob = AllRightBuilder(G, demands, 8).encoded_fixed_paths(wavelengths).construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    # elif args.experiment == "encoded_disjoint_fixed_paths":
    #     bob = AllRightBuilder(G, demands, 8).encoded_fixed_paths(wavelengths, AllRightBuilder.PathType.DISJOINT).construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    # elif  args.experiment == "graph_preproccesing":
    #     bob = AllRightBuilder(G, demands, wavelengths).pruned().construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())    
    # elif args.experiment == "print_demands":
    #     print_demands(args.filename, demands, wavelengths)
    #     exit(0)
    # elif args.experiment == "only_optimal":
    #     bob = AllRightBuilder(G, demands, wavelengths).optimal().construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())  
    # elif args.experiment == "split_graph_baseline": 
    #     bob = AllRightBuilder(G, demands, wavelengths).split().construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    # elif args.experiment == "add_all_split_graph_baseline": 
    #     bob = AllRightBuilder(G, demands, wavelengths).split(True).construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    # elif args.experiment == "split_graph_lim_inc_par":
    #     bob = AllRightBuilder(G, demands, wavelengths).split(True).limited().increasing().construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    # elif args.experiment == "split_graph_fancy_lim_inc_par":
    #     bob = AllRightBuilder(G, demands, wavelengths).split().limited().increasing().construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    # elif args.experiment == "sequence":
    #     bob = AllRightBuilder(G, demands, wavelengths).sequential().construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())
    # elif args.experiment == "increasing":
    #     bob = AllRightBuilder(G, demands, wavelengths).increasing().construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), time.perf_counter() - start_time_rwa)
    # elif args.experiment == "increasing_parallel":
    #     bob = AllRightBuilder(G, demands, wavelengths).increasing().dynamic().construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())    
    # elif args.experiment == "increasing_parallel_sequential":
    #     bob = AllRightBuilder(G, demands, wavelengths).increasing().dynamic().sequential().construct()
    #     (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    else:
        raise Exception("Wrong experiment parameter", parser.print_help())


    end_time_all = time.perf_counter()

    all_time = end_time_all - start_time_all

    print("solve time; all time; satisfiable; size; solution_count; demands; wavelengths")
    print(f"{solve_time};{all_time};{solved};{size};{-1};{args.demands};{wavelengths}")
