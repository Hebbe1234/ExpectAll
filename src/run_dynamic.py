import argparse
import time
from topology import get_demands
from topology import get_nx_graph
from bdd_dynamic import DynamicRWAProblem, AddBlock
from bdd import BDD
rw1 = None
rw2 = None
add = None
def add_last(G, order, demands, wavelengths):
    global rw1, rw2, add
    
    rw1 = DynamicRWAProblem(G, {k:d for k,d in demands.items() if k < len(demands.items()) -1 }, order, wavelengths, init_demand=0)
    start_time_rwa = time.perf_counter()
    rw2 = DynamicRWAProblem(G, {k:d for k,d in demands.items() if k == len(demands.items()) -1 }, order, wavelengths, init_demand=len(rw1.base.demand_vars.keys()))    
    add=AddBlock(rw1,rw2)

    return (start_time_rwa, add)


def add_last_wavelength_constraint(G, order, demands, wavelengths):
    
    rw1 = DynamicRWAProblem(G, {k:d for k,d in demands.items() if k < len(demands.items()) -1 }, order, wavelengths, init_demand=0, generics_first=False, wavelength_constrained=True)
    start_time_rwa = time.perf_counter()
    rw2 = DynamicRWAProblem(G, {k:d for k,d in demands.items() if k == len(demands.items()) -1 }, order, wavelengths, init_demand=len(rw1.base.demand_vars.keys()), generics_first=False, wavelength_constrained=True)    
    add=AddBlock(rw1,rw2)

    return (start_time_rwa, add)

def add_last_wavelength_constraint_n(G, order, demands, wavelengths, n):
    
    rw1 = DynamicRWAProblem(G, {k:d for k,d in demands.items() if k < len(demands.items()) - n }, order, wavelengths, init_demand=0, generics_first=False, wavelength_constrained=True)
    start_time_rwa = time.perf_counter()
    rw2 = DynamicRWAProblem(G, {k:d for k,d in demands.items() if k >= len(demands.items()) - n }, order, wavelengths, init_demand=len(rw1.base.demand_vars.keys()), generics_first=False, wavelength_constrained=True)    
    add=AddBlock(rw1,rw2)

    return (start_time_rwa, add)

def add_all(G,order,demands,wavelengths):
    start_time_rwa = time.perf_counter()
    first_demand = min(list(demands.keys()))

    rw_current = DynamicRWAProblem(G, {first_demand: demands[first_demand]}, order, wavelengths, init_demand=0)

    completed_demands = [first_demand]
    for k,v in demands.items():
        if k == first_demand:
            continue
        rw_next = DynamicRWAProblem(G, {k:v}, order, wavelengths, init_demand=len(completed_demands))
        completed_demands.append(k)
        rw_current=AddBlock(rw_current, rw_next)
    
    return (start_time_rwa, rw_current.expr != rw_current.base.bdd.false)
        
def parallel_add_all(G, order, demands, wavelengths, wc=False):
    rws = []
    rws_next = []
    times = {0:[]}
    n = 1
    for i in range(0, len(demands), n):
        start_time = time.perf_counter()
        rws.append(DynamicRWAProblem(G, {k:d for k,d in demands.items() if i * n <= k and k < i * n + n }, order, wavelengths, init_demand=i * n, group_by_edge_order=True, generics_first=False, wavelength_constrained=wc))

        times[0].append(time.perf_counter() - start_time)
    
    while len(rws) > 1:
        times[len(times)] = []
        rws_next = []
        for i in range(0, len(rws), 2):
            if i + 1 >= len(rws):
                rws_next.append(rws[i])
                break
            start_time = time.perf_counter()
            rws_next.append(AddBlock(rws[i],rws[i+1]))
            times[len(times) - 1].append(time.perf_counter() - start_time)
        
        rws = rws_next
    
    full_time = 0
    for k in times:
        full_time += max(times[k])
    
    return (max(times[len(times) - 1]), full_time, rws[0])
    

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", type=str, help="file to run on")
    parser.add_argument("--wavelengths", default=10, type=int, help="number of wavelengths")
    parser.add_argument("--demands", default=10, type=int, help="number of demands")
    parser.add_argument("--experiment", default="add_last", type=str, help="add_last, add_last_wavelength_constraint, add_last_wavelength_constraint_n, parallel, parallel_wc" )
    args = parser.parse_args()

    G = get_nx_graph(args.filename)
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    demands = get_demands(G, args.demands)
    types = [BDD.ET.EDGE, BDD.ET.LAMBDA, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH,BDD.ET.SOURCE]
    #forced_order = [BDD.ET.LAMBDA, BDD.ET.EDGE, BDD.ET.NODE]
    #ordering = [t for t in types if t not in forced_order]

    solved = False
    full_time = 0
    last_add_time = 0    
    
    start_time_all = time.perf_counter()
    start_time_rwa = time.perf_counter() #bare init. Bliver sat i metoden



    if args.experiment == "add_last":
        (start_time_rwa, rwa) = add_last(G, types, demands, args.wavelengths)
    if args.experiment == "add_last_wavelength_constraint_n":
        demands = get_demands(G, args.wavelengths)
        (start_time_rwa, rwa) = add_last_wavelength_constraint_n(G, types, demands, 8, args.demands) #abusing the dynamic args in run_experiments
    elif args.experiment == "add_last_wavelength_constraint":
        (start_time_rwa, rwa) = add_last_wavelength_constraint(G,types,demands,args.wavelengths)
    elif args.experiment == "parallel":
        (last_add_time, full_time , rwa) = parallel_add_all(G, types, demands, args.wavelengths, False)
    elif args.experiment == "parallel_wc":
        (last_add_time, full_time , rwa) = parallel_add_all(G, types, demands, args.wavelengths, True)
    else: 
        raise Exception("Invalid experiment", args.experiment)
        
    #elif args.experiment == "add_all":
    #    (start_time_rwa, solved) = add_all(G, types, demands, args.wavelengths)

    end_time_all = time.perf_counter()  
    solve_time = end_time_all - start_time_rwa
    all_time = end_time_all - start_time_all

    if full_time > 0:
        solve_time = last_add_time
        all_time = full_time

    print("last demand time;all time;satisfiable;demands;wavelengths")
    print(f"{solve_time};{all_time};{rwa.expr != rwa.base.bdd.false};{len(rwa.base.bdd)};-1;{args.demands};{args.wavelengths}")
