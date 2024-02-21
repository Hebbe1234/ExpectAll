from networkx import MultiDiGraph
import networkx as nx
import matplotlib.pyplot as plt
import pydot
import sys
sys.path.append("../")
import topology
from demands import Demand
from rsa.rsa_bdd import BDD, RSAProblem

def draw_assignment(assignment: dict[str, bool], base: BDD, topology:MultiDiGraph, 
                    demand_to_channels, unique_channels, overlapping_channels):
    color_short_hands = ['blue', 'green', 'yellow', 'brown', 'black', 'purple', 'lightcyan', 'lightgreen', 'pink', 'lightsalmon', 'lime', 'khaki', 'moccasin', 'olive', 'plum', 'peru', 'tan', 'tan2', 'khaki4', 'indigo']
    color_map = {i : color_short_hands[i] for i in range(len(color_short_hands))}
    
    def power(l_var: str):
        val = int(l_var.replace(base.prefixes[BDD.ET.CHANNEL], ""))
        # Total binary vars - var val (hence l1 => |binary vars|)
        exponent =  val - 1
        
        return 2 ** (exponent)
        
    network = nx.create_empty_copy(topology)
    demand_to_chosen_channel = {str(k):0 for k in base.demand_vars.keys()}

    print(base.demand_vars.keys())

    for k, v in assignment.items():
        if k[0] == base.prefixes[BDD.ET.CHANNEL] and v:
            [c_var, demand_id] = k.split("_")
            demand_to_chosen_channel[demand_id] += power(c_var)
    
    edges = {str(v) : k for k , v in base.edge_vars.items()}
    slots_used_on_edges = {k : [] for k in base.edge_vars.keys()}
    
    for k, v in assignment.items():
        if k[0] == base.prefixes[BDD.ET.PATH] and v:
            [p_var, demand_id] = k.split("_")
            (source, target, number) = edges[p_var.replace(base.prefixes[BDD.ET.PATH], "")]
            channel_index = demand_to_chosen_channel[demand_id]
            
            error_found = False
                        
            for channel in slots_used_on_edges[(source, target, number)]:
                if (channel, channel_index) in overlapping_channels:
                    error_found = True
            
            slots_used_on_edges[(source, target, number)].append(channel_index)    
            channel = unique_channels[channel_index]
            
            if not error_found:
                network.add_edge(source, target, label=f"[{channel[0]},{channel[-1]}]", color=color_short_hands[int(demand_id)])
            else:
                network.add_edge(source, target, label=f"[{channel[0]},{channel[-1]}]", color="red", style="dotted")
                print("Error found")
                
    nx.nx_pydot.write_dot(network, "../assignedGraphs/" + "assignedRSA" + ".dot") 
    graphs = pydot.graph_from_dot_file("../assignedGraphs/" + "assignedRSA" + ".dot")   
    if graphs is not None:
        (graph,) = graphs
        graph.del_node('"\\n"')
        graph.write_png("../assignedGraphs/" + "assignedRSA" + ".png")     

if __name__ == "__main__":
  
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../../dot_examples/simple_simple_net.dot"))
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../../dot_examples/simple_net.dot"))
    G = MultiDiGraph(nx.nx_pydot.read_dot("../../dot_examples/four_node.dot"))
    G = topology.get_nx_graph("../" + topology.TOPZOO_PATH +  "/AI3.gml")

    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
        
    num_of_demands = 5
    offset = 0
    seed = 3

    demands = topology.get_gravity_demands(G, num_of_demands, seed)
    ordering = [BDD.ET.EDGE, BDD.ET.CHANNEL, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH, BDD.ET.SOURCE]
    channels = topology.get_channels(demands, number_of_slots=100)
    
    sizes = {d : len(cs[0]) for d, cs in channels.items() if len(cs) > 0}
    print("sizes")
    print(sizes)
    overlapping, unique = topology.get_overlapping_channels(channels)
    
    rsa = RSAProblem(G, demands, ordering, channels, unique, overlapping, 2)

    import time
    print(demands)
    for i in range(1,10000): 
        assignments = rsa.get_assignments(i)
       
        if len(assignments) < i:
            break
        
        draw_assignment(assignments[i-1], rsa.base, G, channels, unique, overlapping)
        # time.sleep(0.01)
        
        

