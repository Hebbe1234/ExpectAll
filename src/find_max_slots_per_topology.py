from fast_rsa_heuristic import calculate_usage, fastHeuristic
from japan_mip_gurubi import SolveJapanMip, run_mip_n
from RSABuilder import AllRightBuilder
import os
from topology import get_channels, get_gravity_demands, get_nx_graph, get_disjoint_simple_paths, get_overlapping_channels,get_safe_upperbound, get_gravity_demands_no_population



top_to_demands_when_infeasible = {}

for file in os.listdir("./topologies/topzoo/"):
    graph = "./topologies/topzoo/" + file
    G = get_nx_graph(graph)
    top_to_demands_when_infeasible[file] = {}
    print(file)

    rest_demands_infseasbile = False

    for num_demands in range(1,30+1):
        if rest_demands_infseasbile:
            top_to_demands_when_infeasible[file][num_demands] = 320
            continue

        demands = get_gravity_demands_no_population(G, num_demands,multiplier=1, seed=20001)

        bob = AllRightBuilder(G, demands, 2, slots=320)

        paths = bob.get_the_damn_paths()
        res, utilized = fastHeuristic(G, demands, paths, 320)
        
        usage = calculate_usage(utilized)
        
        _, _, solved,optimal_number, _, _ = SolveJapanMip(G, demands, paths, usage)

        if solved:
            top_to_demands_when_infeasible[file][num_demands] = optimal_number
            print(num_demands, usage, solved,optimal_number, sum([d.size for d in demands.values()]))
        else:
            rest_demands_infseasbile = True


import json
with open('data.json', 'w') as f:
    json.dump(top_to_demands_when_infeasible, f)



    
