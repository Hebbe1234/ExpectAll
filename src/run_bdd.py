import argparse
import time
import topology
from bdd import RWAProblem, BDD
from topology import get_demands
from topology import get_nx_graph

rw = None

def baseline(G, order, demands, wavelengths):
    global rw
    rw = RWAProblem(G, demands, order, wavelengths, group_by_edge_order =True, generics_first=False, with_sequence=False)
    return (rw.rwa != rw.base.bdd.false, len(rw.base.bdd))

def reordering(G, demands, wavelengths, good=True):
    global rw
    if good:
        forced_order = [BDD.ET.EDGE, BDD.ET.LAMBDA, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH,BDD.ET.SOURCE]
        rw = RWAProblem(G, demands, forced_order, wavelengths, group_by_edge_order =True, generics_first=False, with_sequence=False, reordering=True)
    else: 
        forced_order = [BDD.ET.NODE, BDD.ET.TARGET, BDD.ET.SOURCE, BDD.ET.PATH, BDD.ET.LAMBDA, BDD.ET.EDGE,BDD.ET.DEMAND]
        rw = RWAProblem(G, demands, forced_order, wavelengths, group_by_edge_order =True, generics_first=True, with_sequence=False, reordering=True)


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

def best(G, order, demands, wavelengths):
    global rw
    wavelengths = [1,2] + [w for w in range(4, wavelengths+1) if w%4 == 0]
    for w in wavelengths:
        print(f"w: {w}")
        rw = RWAProblem(G, demands, order, w, group_by_edge_order=True, generics_first=False, with_sequence=False, wavelength_constrained=True)
        if rw.rwa != rw.base.bdd.false:
            return (True, len(rw.base.bdd))
    
    if rw is not None:
        return (False, len(rw.base.bdd))
    
    return (False, 0)


def print_demands(filename, demands, wavelengths):
    print("graph: ", filename, "wavelengths: ", wavelengths, "demands: ")
    print(demands)

def wavelengths_static_demand(G, forced_order, ordering, demands, wavelengths):
    return baseline(G, forced_order+[*ordering], demands, wavelengths)
    

def wavelength_constrained(G, order, demands, wavelengths):
    global rw

    rw = RWAProblem(G, demands, order, wavelengths, group_by_edge_order =True, generics_first=False, with_sequence=False, wavelength_constrained=True)
    return (rw.rwa != rw.base.bdd.false, len(rw.base.bdd))

def sequence(G, order, demands, wavelengths):
    global rw

    rw = RWAProblem(G, demands, order, wavelengths, group_by_edge_order =True, generics_first=False, with_sequence=True)
    return (rw.rwa != rw.base.bdd.false, len(rw.base.bdd))

def unary(G, order, demands, wavelengths):
    global rw 
    rw = RWAProblem(G, demands, order, wavelengths, group_by_edge_order =True, generics_first=False, with_sequence=False, binary=False)


    return (rw.rwa != rw.base.bdd.false, len(rw.base.bdd))

#def find_optimal(G,order,demands,wavelengths):

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
    
    start_time_rwa = time.perf_counter()

    if args.experiment == "baseline":
        (solved, size) = baseline(G, forced_order+[*ordering], demands, args.wavelengths)
    elif args.experiment == "increasing":
        (solved, size) = increasing(G, forced_order+[*ordering], demands, args.wavelengths)
    elif args.experiment == "wavelength_constraint":
        (solved, size) = wavelength_constrained(G, forced_order+[*ordering], demands, args.wavelengths)
    elif args.experiment == "print_demands":
        print_demands(args.filename, demands, args.wavelengths)
        exit(0)
    elif args.experiment == "wavelengths_static_demands":
        (solved, size) = wavelengths_static_demand(G, forced_order, ordering, demands, args.wavelengths)
    elif args.experiment == "unary":
        (solved, size) = unary(G, forced_order+[*ordering], demands, args.wavelengths)
    elif args.experiment == "sequence":
            (solved, size) = sequence(G, forced_order+[*ordering], demands, args.wavelengths)
    elif args.experiment == "default_reordering":
            (solved, size) = reordering(G, demands, args.wavelengths, True)
    elif args.experiment == "default_reordering_bad":
            (solved, size) = reordering(G, demands, args.wavelengths, False)
    elif args.experiment == "best":
            (solved, size) = best(G, forced_order+[*ordering], demands, args.wavelengths)
    else:
        raise Exception("Wrong experiment parameter", parser.print_help())

    
    end_time_all = time.perf_counter()  

    solve_time = end_time_all - start_time_rwa
    all_time = end_time_all - start_time_all
    print("solve time; all time; satisfiable; demands; wavelengths")
    print(f"{solve_time};{all_time};{solved};{size};{-1};{args.demands};{args.wavelengths}")
