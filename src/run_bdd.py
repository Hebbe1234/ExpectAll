import argparse
import time
from RSABuilder import AllRightBuilder
from topology import get_gravity_demands, get_nx_graph, get_gravity_demands2_nodes_have_constant_size, generate_n_node_graph_and_demands
from demand_ordering import demand_order_sizes
from topology import generate_n_node_1_demands

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
    args = parser.parse_args()

    wavelengths = args.wavelengths
    G = 1
    graph, demands, graph_overlap, demand_overlap = 0,0,0,0
    if "synth" not in args.filename:

        G = get_nx_graph(args.filename)
        if G.nodes.get("\\n") is not None:
            G.remove_node("\\n")
        demands = get_gravity_demands2_nodes_have_constant_size(G, args.demands)
        demands = demand_order_sizes(demands)
    elif "synth" in args.filename:
        graph, demands, graph_overlap, demand_overlap = generate_n_node_graph_and_demands(args.demands)
    elif "naiv2" in args.filename:
        graph, demands = generate_n_node_1_demands(args.demands, 2)


    
    solved = False
    size = 0
    solve_time = 0

    print(demands)
    
    start_time_all = time.perf_counter()

    if args.experiment == "baseline_v2":
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



    elif(args.experiment == "synth1"):
        bob1 = AllRightBuilder(graph, demands, wavelengths).limited().path_type(AllRightBuilder.PathType.DISJOINT).construct()
        (solved, size, solve_time) = (bob1.solved(), bob1.size(), bob1.get_build_time())  
    elif(args.experiment == "synth2"): 
        bob2 = AllRightBuilder(graph_overlap, demand_overlap, wavelengths).limited().path_type(AllRightBuilder.PathType.DISJOINT).construct()
        (solved, size, solve_time) = (bob2.solved(), bob2.size(), bob2.get_build_time())  
    elif(args.experiment == "naiv2"):
        bob1 = AllRightBuilder(graph, demands, wavelengths).limited().path_type(AllRightBuilder.PathType.DISJOINT).construct()
        (solved, size, solve_time) = (bob1.solved(), bob1.size(), bob1.get_build_time())  
        
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
