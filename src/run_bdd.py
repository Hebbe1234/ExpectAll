import argparse
import time

import networkx
from RWABuilder import AllRightBuilder
import topology
from bdd import RWAProblem, BDD, OnlyOptimalBlock
from bdd_path_vars import RWAProblem as RWAProblem_path_vars, BDD as PBDD
from bdd_edge_encoding import RWAProblem as RWAProblem_EE, BDD as BDD_EE
from rsa.rsa_bdd import RSAProblem, BDD as RSABDD
from topology import get_demands, get_gravity_demands
from topology import get_nx_graph, split_into_multiple_graphs, split_demands
from run_dynamic import parallel_add_all
from split_graph_dem_bdd import AddBlock, SplitRWAProblem2, SplitBDD2, AddAllBlock
rw = None
rsa = None


def split_graph_fancy_lim_inc_par(G, order, demands, wavelengths):
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
    if subgraphs is None or removedNode is None: 
        raise Exception("graph is unsplitable")    
    times = []
    for w in range(1,wavelengths+1):
        start_time = time.perf_counter()

        graphToNewDemands = topology.split_demands2(G, subgraphs, removedNode, oldDemands)

        types = [BDD.ET.EDGE, BDD.ET.LAMBDA, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH, BDD.ET.SOURCE]
        solutions = []  
        
        for g in subgraphs: 
            if g in graphToNewDemands:
                demands = graphToNewDemands[g]
                rw1 = SplitRWAProblem2(g, demands, types, w, group_by_edge_order=True, generics_first=False, reordering=True, wavelength_constrained=True)
                solutions.append(rw1)
            else: 
                pass
        before_add = time.perf_counter()
        rw=AddBlock(G, solutions, oldDemands, graphToNewDemands)
        times.append(time.perf_counter() - start_time)
        if rw.validSolutions == True:
            print("fancy add: ", time.perf_counter() - before_add)
            return (True, len(rw.base.bdd), max(times))  

    if rw is not None:
        return(False, len(rw.base.bdd), max(times))
    
    return (False, 0,0)


def split_graph_lim_inc_par(G, order, demands, wavelengths):
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
    if subgraphs is None or removedNode is None: 
        raise Exception("graph is unsplitable")    
    times = []
    for w in range(1,wavelengths+1):
        start_time = time.perf_counter()

        newDemandsDict , oldDemandsToNewDemands, graphToNewDemands = topology.split_demands(G, subgraphs, removedNode, oldDemands)
        graphToNewDemands = topology.split_demands2(G, subgraphs, removedNode, oldDemands)

        types = [BDD.ET.EDGE, BDD.ET.LAMBDA, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH, BDD.ET.SOURCE]
        solutions = []  
        
        for g in subgraphs: 
            if g in graphToNewDemands:
                demands = graphToNewDemands[g]
                rw1 = SplitRWAProblem2(g, demands, types, w, group_by_edge_order=True, generics_first=False, reordering=True, wavelength_constrained=True)
                solutions.append(rw1)
            else: 
                pass
        before_add = time.perf_counter()
        rw=AddAllBlock(G, solutions, oldDemands, graphToNewDemands)
        times.append(time.perf_counter() - start_time)

        if rw.expr != rw.base.bdd.false:
            print("normal add:", time.perf_counter() - before_add)
            return (True, len(rw.base.bdd), max(times))  

    if rw is not None:
        return(False, len(rw.base.bdd), max(times))
    
    return (False, 0,0)


def split_graph_baseline(G, order, demands, wavelengths):
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
        print("with baseline")
    
        return (None, None)
        rw = RWAProblem(G, demands, order, wavelengths, group_by_edge_order =True, generics_first=False, with_sequence=False, reordering=True)
        return (rw.rwa != rw.base.bdd.false, len(rw.base.bdd))

    newDemandsDict , oldDemandsToNewDemands, graphToNewDemands = topology.split_demands(G, subgraphs, removedNode, oldDemands)
    graphToNewDemands = topology.split_demands2(G, subgraphs, removedNode, oldDemands)

    types = [BDD.ET.EDGE, BDD.ET.LAMBDA, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH, BDD.ET.SOURCE]
    solutions = []  
    
    start_all = time.perf_counter()
    for g in subgraphs: 
        if g in graphToNewDemands:
            demands = graphToNewDemands[g]
            rw1 = SplitRWAProblem2(g, demands, types, wavelengths, group_by_edge_order=True, generics_first=False, reordering=True)
            solutions.append(rw1)
        else: 
            pass
    start_add = time.perf_counter()
    rw=AddBlock(G, solutions, oldDemands, graphToNewDemands)
    end_all = time.perf_counter()
    print("time subs: ", start_add - start_all)
    print("time add: ", end_all - start_add)
    print("percent sub: ", 100*(start_add - start_all)/ (end_all - start_all) )
    print("percent add: ", 100*(end_all - start_add)/ (end_all - start_all) )

    
    return (rw.expr != rw.base.bdd.false, len(rw.base.bdd))  

def add_all_split_graph_baseline(G, order, demands, wavelengths):
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
        print("with baseline")
    
        return (None, None)
        rw = RWAProblem(G, demands, order, wavelengths, group_by_edge_order =True, generics_first=False, with_sequence=False, reordering=True)
        return (rw.rwa != rw.base.bdd.false, len(rw.base.bdd))

    newDemandsDict , oldDemandsToNewDemands, graphToNewDemands = topology.split_demands(G, subgraphs, removedNode, oldDemands)
    graphToNewDemands = topology.split_demands2(G, subgraphs, removedNode, oldDemands)

    types = [BDD.ET.EDGE, BDD.ET.LAMBDA, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH, BDD.ET.SOURCE]
    solutions = []  
    
    start_all = time.perf_counter()
    for g in subgraphs: 
        if g in graphToNewDemands:
            demands = graphToNewDemands[g]
            rw1 = SplitRWAProblem2(g, demands, types, wavelengths, group_by_edge_order=True, generics_first=False, reordering=True)
            solutions.append(rw1)
        else: 
            pass
    start_add = time.perf_counter()
    rw=AddAllBlock(G, solutions, oldDemands, graphToNewDemands)
    end_all = time.perf_counter()
    print("time subs: ", start_add - start_all)
    print("time add: ", end_all - start_add)
    print("percent sub: ", 100*(start_add - start_all)/ (end_all - start_all) )
    print("percent add: ", 100*(end_all - start_add)/ (end_all - start_all) )

    
    return (rw.expr != rw.base.bdd.false, len(rw.base.bdd))  

def baseline(G, order, demands, wavelengths, sequential=False):
    global rw
    rw = RWAProblem(G, demands, order, wavelengths, group_by_edge_order =True, generics_first=False, with_sequence=sequential)
    return (rw.rwa != rw.base.bdd.false, len(rw.base.bdd))

def baseline_graph_preprocessed(G, order, demands, wavelengths, sequential=False):
    global rw
    new_graph = topology.reduce_graph_based_on_demands(G, demands)
    rw = RWAProblem(new_graph, demands, order, wavelengths, group_by_edge_order =True, generics_first=False, with_sequence=sequential)
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
    overlapping_paths = topology.get_overlapping_simple_paths(paths)
    rw = RWAProblem_path_vars(G, demands, paths, overlapping_paths, order, wavelengths, group_by_edge_order =True, generics_first=False)
    return (rw.rwa != rw.base.bdd.false, len(rw.base.bdd))

def encoded_quote_on_quote_disjoint_fixed_paths_inc_par_seq(G, order, demands, wavelengths, sequential, k):
    global rw
    times = []
    order = [PBDD.ET.EDGE, PBDD.ET.LAMBDA, PBDD.ET.NODE, PBDD.ET.DEMAND, PBDD.ET.TARGET, PBDD.ET.PATH, PBDD.ET.SOURCE]
    paths = topology.get_disjoint_simple_paths(G, demands, k)
    overlapping_paths = topology.get_overlapping_simple_paths(paths)
    
    for w in range(1,wavelengths+1):
        start_time = time.perf_counter()
        rw = RWAProblem_path_vars(G, demands, paths, overlapping_paths, order, w, group_by_edge_order =True, generics_first=False, with_sequence=sequential, reordering=True)
        
        times.append(time.perf_counter() - start_time)

        if rw.rwa != rw.base.bdd.false:
            return (True, len(rw.base.bdd), max(times))

    if rw is not None:
        return (False, len(rw.base.bdd), max(times))

    return (False, 0, 0)

def encoded_fixed_paths_inc_par_sequential(G, order, demands, wavelengths, sequential, k):
    global rw    
    times = []
    order = [PBDD.ET.EDGE, PBDD.ET.LAMBDA, PBDD.ET.NODE, PBDD.ET.DEMAND, PBDD.ET.TARGET, PBDD.ET.PATH, PBDD.ET.SOURCE]
    paths = topology.get_simple_paths(G, demands, k)
    overlapping_paths = topology.get_overlapping_simple_paths(paths)
    
    for w in range(1,wavelengths+1):
        start_time = time.perf_counter()
        rw = RWAProblem_path_vars(G, demands, paths, overlapping_paths, order, w, group_by_edge_order =True, generics_first=False, with_sequence=sequential, reordering=True)
        
        times.append(time.perf_counter() - start_time)

        if rw.rwa != rw.base.bdd.false:
            return (True, len(rw.base.bdd), max(times))

    if rw is not None:
        return (False, len(rw.base.bdd), max(times))

    return (False, 0, 0)


def encoded_fixed_paths_inc_par_sequential_clique(G, order, demands, wavelengths, sequential, k):
    global rw
    times = []
    order = [PBDD.ET.EDGE, PBDD.ET.LAMBDA, PBDD.ET.NODE, PBDD.ET.DEMAND, PBDD.ET.TARGET, PBDD.ET.PATH, PBDD.ET.SOURCE]
    paths = topology.get_simple_paths(G, demands, k)
    overlapping_paths = topology.get_overlapping_simple_paths(paths)
    cliques = topology.get_overlap_cliques(list(demands.values()), paths)

    for w in range(1,wavelengths+1):
        start_time = time.perf_counter()
        rw = RWAProblem_path_vars(G, demands, paths, overlapping_paths, order, w, group_by_edge_order =True, generics_first=False, with_sequence=sequential, reordering=True, cliques=cliques)
        
        times.append(time.perf_counter() - start_time)

        if rw.rwa != rw.base.bdd.false:
            return (True, len(rw.base.bdd), max(times))

    if rw is not None:
        return (False, len(rw.base.bdd), max(times))

    return (False, 0, 0)

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

    demands = get_gravity_demands(G, args.demands)
    types = [BDD.ET.LAMBDA, BDD.ET.DEMAND, BDD.ET.EDGE, BDD.ET.SOURCE, BDD.ET.TARGET, BDD.ET.NODE, BDD.ET.PATH]
    start_time_all = time.perf_counter()

    forced_order = [BDD.ET.EDGE, BDD.ET.LAMBDA, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH,BDD.ET.SOURCE]
    ordering = [t for t in types if t not in forced_order]

    
    solved = False
    size = 0
    solve_time = 0

    start_time_rwa = time.perf_counter()

    if args.experiment == "baseline":
        bob = AllRightBuilder(G, demands, args.wavelengths).construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())
    elif args.experiment == "sequence":
        bob = AllRightBuilder(G, demands, args.wavelengths).sequential().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())
    elif args.experiment == "increasing":
        bob = AllRightBuilder(G, demands, args.wavelengths).increasing().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), time.perf_counter() - start_time_rwa)
    elif args.experiment == "increasing_parallel":
        bob = AllRightBuilder(G, demands, args.wavelengths).increasing().dynamic().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())    
    elif args.experiment == "increasing_parallel_sequential":
        bob = AllRightBuilder(G, demands, args.wavelengths).increasing().dynamic().sequential().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    elif(args.experiment == "encoded_paths_increasing_parallel_sequential"):
        bob = AllRightBuilder(G, demands, 8).encoded_fixed_paths(args.wavelength).increasing().sequential().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())         
    elif args.experiment == "encoded_disjoint_fixed_paths_inc_par_sec":
        bob = AllRightBuilder(G, demands, 8).encoded_fixed_paths(args.wavelength, AllRightBuilder.PathType.DISJOINT).increasing().sequential().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())  
    elif args.experiment == "encoded_fixed_paths_inc_par_seq_cliq":
        bob = AllRightBuilder(G, demands, 8).encoded_fixed_paths(args.wavelength).increasing().sequential().clique().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())  
    elif args.experiment == "encoded_3_fixed_paths_inc_par_seq":
        bob = AllRightBuilder(G, demands, args.wavelength).encoded_fixed_paths(3).increasing().sequential().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())      
    elif args.experiment == "encoded_3_fixed_paths_inc_par_seq_clique":
        bob = AllRightBuilder(G, demands, args.wavelength).encoded_fixed_paths(3).increasing().sequential().clique().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())  
    elif args.experiment == "increasing_parallel_sequential_reordering":
        bob = AllRightBuilder(G, demands, args.wavelengths).increasing().sequential().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())        
    elif args.experiment == "increasing_parallel_dynamic_limited":
        bob = AllRightBuilder(G, demands, args.wavelengths).increasing().dynamic().limited().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    elif args.experiment == "dynamic_limited":
        bob = AllRightBuilder(G, demands, args.wavelengths).dynamic().limited().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    elif args.experiment == "wavelength_constraint":
        bob = AllRightBuilder(G, demands, args.wavelengths).limited().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    elif args.experiment == "naive_fixed_paths":
        bob = AllRightBuilder(G, demands, 8).naive_fixed_paths(args.wavelengths).construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    elif args.experiment == "encoded_fixed_paths":
        bob = AllRightBuilder(G, demands, 8).encoded_fixed_paths(args.wavelengths).construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    elif args.experiment == "encoded_disjoint_fixed_paths":
        bob = AllRightBuilder(G, demands, 8).encoded_fixed_paths(args.wavelengths, AllRightBuilder.PathType.DISJOINT).construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    elif  args.experiment == "graph_preproccesing":
        bob = AllRightBuilder(G, demands, args.wavelength).pruned().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())    
    elif args.experiment == "rsa_baseline":
        demands = topology.get_gravity_demands(G, args.demands)
        bob = AllRightBuilder(G, demands, args.wavelength).channels().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time())  
    elif args.experiment == "rsa_inc_par_lim":
        bob = AllRightBuilder(G, demands, args.wavelength).channels().limited().increasing().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    elif args.experiment == "rsa_inc_par":
        bob = AllRightBuilder(G, demands, args.wavelength).channels().increasing().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
    elif args.experiment == "rsa_lim":
        bob = AllRightBuilder(G, demands, args.wavelength).channels().limited().construct()
        (solved, size, solve_time) = (bob.solved(), bob.size(), bob.get_build_time()) 
  
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
    elif args.experiment == "add_all_split_graph_baseline": 
        (solved, size) = add_all_split_graph_baseline(G,forced_order+[*ordering],demands,args.wavelengths)
    elif args.experiment == "split_graph_lim_inc_par":
        (solved, size, solve_time) = split_graph_lim_inc_par(G,forced_order+[*ordering],demands,args.wavelengths)
    elif args.experiment == "split_graph_fancy_lim_inc_par":
        (solved, size, solve_time) = split_graph_fancy_lim_inc_par(G,forced_order+[*ordering],demands,args.wavelengths)
    else:
        raise Exception("Wrong experiment parameter", parser.print_help())


    end_time_all = time.perf_counter()

    all_time = end_time_all - start_time_all

    if solve_time == 0:
        print("Here")
        solve_time = end_time_all - start_time_rwa


    print("solve time; all time; satisfiable; demands; wavelengths")
    print(f"{solve_time};{all_time};{solved};{size};{-1};{args.demands};{args.wavelengths}")
