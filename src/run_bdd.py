import argparse
import time
import topology
from bdd import RWAProblem, BDD, OnlyOptimalBlock
from bdd_path_vars import RWAProblem as RWAProblem_path_vars, BDD as PBDD
from bdd_edge_encoding import RWAProblem as RWAProblem_EE, BDD as BDD_EE
from topology import get_demands
from topology import get_nx_graph, split_into_multiple_graphs, split_demands
from run_dynamic import parallel_add_all
from split_graph_dem_bdd import AddBlock, SplitRWAProblem2, SplitBDD2
rw = None

def split_graph_baseline(G, order, demands, wavelengths, sequential=False):
    global rw
    oldDemands = demands
    import topology
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
    for i,n in enumerate(G.nodes):
        G.nodes[n]['id'] = i
    for i,e in enumerate(G.edges):
        G.edges[e]['id'] = i

    subgraphs, removedNode = topology.split_into_multiple_graphs(G)
    if subgraphs == None or removedNode == None: 
        rw = RWAProblem(G, demands, order, wavelengths, group_by_edge_order =True, generics_first=False, with_sequence=sequential, reordering=True)
        return (rw.rwa != rw.base.bdd.false, len(rw.base.bdd))

    newDemandsDict , oldDemandsToNewDemands, graphToNewDemands = topology.split_demands(G, subgraphs, removedNode, oldDemands)
    graphToNewDemands = topology.split_demands2(G, subgraphs, removedNode, oldDemands)

    types = [BDD.ET.EDGE, BDD.ET.LAMBDA, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH, BDD.ET.SOURCE]
    solutions = []  
    
    
    for g in subgraphs: 
        if g in graphToNewDemands:
            demands = graphToNewDemands[g]
            rw1 = SplitRWAProblem2(g, demands, types, wavelengths, group_by_edge_order=True, generics_first=False)
            solutions.append(rw1)
        else: 
            pass
    rw=AddBlock(G, solutions, oldDemands, graphToNewDemands)
    return (rw.expr != rw.base.bdd.false, len(rw.base.bdd))  


def baseline(G, order, demands, wavelengths, sequential=False):
    global rw
    rw = RWAProblem(G, demands, order, wavelengths, group_by_edge_order =True, generics_first=False, with_sequence=sequential)
    return (rw.rwa != rw.base.bdd.false, len(rw.base.bdd))

def reordering(G, demands, wavelengths, good=True):
    global rw
    if good:
        #forced_order = [BDD.ET.LAMBDA, BDD.ET.DEMAND, BDD.ET.SOURCE, BDD.ET.EDGE, BDD.ET.NODE, BDD.ET.PATH,BDD.ET.SOURCE]
        forced_order = [BDD.ET.EDGE, BDD.ET.LAMBDA, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH, BDD.ET.SOURCE]
        rw = RWAProblem(G, demands, forced_order, wavelengths, group_by_edge_order =True, generics_first=False, with_sequence=False, reordering=True)
    else:
        forced_order = [BDD.ET.NODE, BDD.ET.TARGET, BDD.ET.SOURCE, BDD.ET.PATH, BDD.ET.LAMBDA, BDD.ET.EDGE,BDD.ET.DEMAND]
        rw = RWAProblem(G, demands, forced_order, wavelengths, group_by_edge_order =True, generics_first=True, with_sequence=False, reordering=True)


    return (rw.rwa != rw.base.bdd.false, len(rw.base.bdd))

def reordering_edge_encoding(G, demands, wavelengths, good=True):
    global rw
    if good:
        forced_order = [BDD_EE.ET.DEMAND, BDD_EE.ET.SOURCE, BDD_EE.ET.EDGE, BDD_EE.ET.NODE, BDD_EE.ET.PATH, BDD_EE.ET.TARGET]
        rw = RWAProblem_EE(G, demands, forced_order, wavelengths, group_by_edge_order =True, generics_first=False, with_sequence=False, reordering=True)
    else:
        forced_order = [BDD_EE.ET.NODE, BDD_EE.ET.TARGET, BDD_EE.ET.PATH, BDD_EE.ET.SOURCE, BDD_EE.ET.EDGE, BDD_EE.ET.DEMAND]
        rw = RWAProblem_EE(G, demands, forced_order, wavelengths, group_by_edge_order =True, generics_first=True, with_sequence=False, reordering=True)


    return (rw.rwa != rw.base.bdd.false, len(rw.base.bdd))

def increasing(G, order, demands, wavelengths):
    global rw

    for w in range(1,wavelengths+1):
        print(f"w: {w}")
        rw = RWAProblem(G, demands, order, w, group_by_edge_order =True, generics_first=False, with_sequence=False)
        if rw.rwa != rw.base.bdd.false:
            return (True, len(rw.base.bdd))

    if rw is not None:
        return (False, len(rw.base.bdd))

    return (False, 0)

def increasing_parallel(G, order, demands, wavelengths, sequential, reordering=False):
    global rw
    times = []
    for w in range(1,wavelengths+1):
        start_time = time.perf_counter()
        rw = RWAProblem(G, demands, order, w, group_by_edge_order =True, generics_first=False, with_sequence=sequential, reordering=reordering)
        
        times.append(time.perf_counter() - start_time)

        if rw.rwa != rw.base.bdd.false:
            return (True, len(rw.base.bdd), max(times))

    if rw is not None:
        return (False, len(rw.base.bdd), max(times))

    return (False, 0, 0)


def increasing_parallel_dynamic_limited(G, order, demands, wavelengths):
    global rw
    times = []
    for w in range(1,wavelengths+1):
        (last_time, full_time, rw) = parallel_add_all(G, order, demands, w, True)
        
        times.append(full_time)

        if rw.expr != rw.base.bdd.false:
            return (True, len(rw.base.bdd), max(times))

    if rw is not None:
        return (False, len(rw.base.bdd), max(times))

    return (False, 0, 0)

def dynamic_limited(G, order, demands, wavelengths):
    global rw
    (last_time, full_time, rw) = parallel_add_all(G, order, demands, wavelengths, True)
    return (rw.expr != rw.base.bdd.false, len(rw.base.bdd), full_time)

# def best(G, order, demands, wavelengths):
#     global rw
#     wavelengths = [1,2] + [w for w in range(4, wavelengths+1) if w%4 == 0]
#     for w in wavelengths:
#         print(f"w: {w}")
#         rw = RWAProblem(G, demands, order, w, group_by_edge_order=True, generics_first=False, with_sequence=False, wavelength_constrained=True)
#         if rw.rwa != rw.base.bdd.false:
#             return (True, len(rw.base.bdd))

#     if rw is not None:
#         return (False, len(rw.base.bdd))

#     return (False, 0)

def naive_fixed_paths(G, order, demands, wavelengths, k):
    global rw
    paths = topology.get_simple_paths(G, demands, k)
    rw = RWAProblem(G, demands, order, wavelengths, group_by_edge_order =True, generics_first=False, paths=paths)
    return (rw.rwa != rw.base.bdd.false, len(rw.base.bdd))

def encoded_fixed_paths(G, order, demands, wavelengths, k):
    global rw
    order = [PBDD.ET.EDGE, PBDD.ET.LAMBDA, PBDD.ET.NODE, PBDD.ET.DEMAND, PBDD.ET.TARGET, PBDD.ET.PATH, PBDD.ET.SOURCE]
    paths = topology.get_simple_paths(G, demands, k)
    overlapping_paths = topology.get_overlapping_simple_paths(G, paths)
    rw = RWAProblem_path_vars(G, demands, paths, overlapping_paths, order, wavelengths, group_by_edge_order =True, generics_first=False)
    return (rw.rwa != rw.base.bdd.false, len(rw.base.bdd))

def print_demands(filename, demands, wavelengths):
    print("graph: ", filename, "wavelengths: ", wavelengths, "demands: ")
    print(demands)

def wavelengths_static_demand(G, forced_order, ordering, demands, wavelengths):
    return baseline(G, forced_order+[*ordering], demands, wavelengths)


def wavelength_constrained(G, order, demands, wavelengths):
    global rw

    rw = RWAProblem(G, demands, order, wavelengths, group_by_edge_order =True, generics_first=False, with_sequence=False, wavelength_constrained=True)
    return (rw.rwa != rw.base.bdd.false, len(rw.base.bdd))

def unary(G, order, demands, wavelengths):
    global rw
    rw = RWAProblem(G, demands, order, wavelengths, group_by_edge_order =True, generics_first=False, with_sequence=False, binary=False)

    return (rw.rwa != rw.base.bdd.false, len(rw.base.bdd))

def find_optimal(G,order,demands,wavelengths):
    global rw
    rw = RWAProblem(G,demands,order,wavelengths,group_by_edge_order=True, generics_first=False, wavelength_constrained=False, with_sequence=False, only_optimal=True)

    return (rw.rwa != rw.base.bdd.false, len(rw.base.bdd))

if __name__ == "__main__":
    parser = argparse.ArgumentParser("mainbdd.py")
    parser.add_argument("--filename", type=str, help="file to run on")
    parser.add_argument("--wavelengths", default=10, type=int, help="number of wavelengths")
    parser.add_argument("--demands", default=10, type=int, help="number of demands")
    parser.add_argument("--experiment", default="baseline", type=str, help="baseline, increasing, wavelength_constraint, print_demands, wavelengths_static_demands, default_reordering, unary, sequence")
    args = parser.parse_args()

    G = get_nx_graph(args.filename)
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    demands = get_demands(G, args.demands)
    types = [BDD.ET.LAMBDA, BDD.ET.DEMAND, BDD.ET.EDGE, BDD.ET.SOURCE, BDD.ET.TARGET, BDD.ET.NODE, BDD.ET.PATH]
    start_time_all = time.perf_counter()

    forced_order = [BDD.ET.EDGE, BDD.ET.LAMBDA, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH,BDD.ET.SOURCE]
    ordering = [t for t in types if t not in forced_order]

    solved = False
    size = 0
    full_time = 0

    start_time_rwa = time.perf_counter()

    if args.experiment == "baseline":
        (solved, size) = baseline(G, forced_order+[*ordering], demands, args.wavelengths)
    elif args.experiment == "sequence":
        (solved, size) = baseline(G, forced_order+[*ordering], demands, args.wavelengths, True)
    elif args.experiment == "increasing":
        (solved, size) = increasing(G, forced_order+[*ordering], demands, args.wavelengths)
    elif args.experiment == "increasing_parallel":
        (solved, size, full_time) = increasing_parallel(G, forced_order+[*ordering], demands, args.wavelengths, False)
    elif args.experiment == "increasing_parallel_sequential":
        (solved, size, full_time) = increasing_parallel(G, forced_order+[*ordering], demands, args.wavelengths, True)
    elif args.experiment == "increasing_parallel_sequential_reordering":
        (solved, size, full_time) = increasing_parallel(G, forced_order+[*ordering], demands, args.wavelengths, True, True)
    elif args.experiment == "increasing_parallel_dynamic_limited":
        (solved, size, full_time) = increasing_parallel_dynamic_limited(G, forced_order+[*ordering], demands, args.wavelengths)
    elif args.experiment == "dynamic_limited":
        (solved, size, full_time) = dynamic_limited(G, forced_order+[*ordering], demands, args.wavelengths)
    elif args.experiment == "wavelength_constraint":
        (solved, size) = wavelength_constrained(G, forced_order+[*ordering], demands, args.wavelengths)
    elif args.experiment == "naive_fixed_paths":
        (solved, size) = naive_fixed_paths(G, forced_order+[*ordering], demands, 8, args.wavelengths)
    elif args.experiment == "encoded_fixed_paths":
        (solved, size) = encoded_fixed_paths(G, forced_order+[*ordering], demands, 8, args.wavelengths)
    elif args.experiment == "print_demands":
        print_demands(args.filename, demands, args.wavelengths)
        exit(0)
    elif args.experiment == "wavelengths_static_demands":
        (solved, size) = wavelengths_static_demand(G, forced_order, ordering, demands, args.wavelengths)
    elif args.experiment == "unary":
        (solved, size) = unary(G, forced_order+[*ordering], demands, args.wavelengths)
    elif args.experiment == "default_reordering":
        (solved, size) = reordering(G, demands, args.wavelengths, True)
    elif args.experiment == "default_reordering_bad":
        (solved, size) = reordering(G, demands, args.wavelengths, False)
    elif args.experiment == "default_reordering_ee":
        (solved, size) = reordering_edge_encoding(G, demands, args.wavelengths, True)
    elif args.experiment == "default_reordering_ee_bad":
        (solved, size) = reordering_edge_encoding(G, demands, args.wavelengths, False)
    # elif args.experiment == "best":
    #     (solved, size) = best(G, forced_order+[*ordering], demands, args.wavelengths)
    elif args.experiment == "only_optimal":
        (solved, size) = find_optimal(G,forced_order+[*ordering],demands,args.wavelengths)
    elif args.experiment == "split_graph_baseline": 
        (solved, size) = split_graph_baseline(G,forced_order+[*ordering],demands,args.wavelengths)

    else:
        raise Exception("Wrong experiment parameter", parser.print_help())


    end_time_all = time.perf_counter()

    solve_time = end_time_all - start_time_rwa
    all_time = end_time_all - start_time_all

    if full_time > 0:
        print("Here")
        solve_time = full_time

    print("solve time; all time; satisfiable; demands; wavelengths")
    print(f"{solve_time};{all_time};{solved};{size};{-1};{args.demands};{args.wavelengths}")
