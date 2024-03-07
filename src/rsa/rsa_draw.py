from networkx import MultiDiGraph
import networkx as nx
import matplotlib.pyplot as plt
import pydot
import sys
sys.path.append("../")
import topology
from demands import Demand
from rsa.rsa_bdd import BDD, RSAProblem
#from RSABuilder import ET, prefixes
# from RSABuilder import AllRightBuilder
color_short_hands = ['blue', 'green', 'yellow', 'brown', 'black', 'purple', 'lightcyan', 'lightgreen', 'pink', 'lightsalmon', 'lime', 'khaki', 'moccasin', 'olive', 'plum', 'peru', 'tan', 'tan2', 'khaki4', 'indigo']
color_map = {i : color_short_hands[i] for i in range(len(color_short_hands))}

def draw_assignment(assignment: dict[str, bool], base, topology:MultiDiGraph, 
                    demand_to_channels, unique_channels, overlapping_channels, file_path="../assignedGraphs/assignedRSA"):
    
    def power(l_var: str):
        val = int(l_var.replace(prefixes[ET.CHANNEL], ""))
        # Total binary vars - var val (hence l1 => |binary vars|)
        exponent =  val - 1
        
        return 2 ** (exponent)
        
    network = nx.create_empty_copy(topology)
    demand_to_chosen_channel = {str(k):0 for k in base.demand_vars.keys()}

    print(base.demand_vars.keys())

    for k, v in assignment.items():
        if k[0] == prefixes[ET.CHANNEL] and v:
            [c_var, demand_id] = k.split("_")
            demand_to_chosen_channel[demand_id] += power(c_var)
    
    edges = {str(v) : k for k , v in base.edge_vars.items()}
    slots_used_on_edges = {k : [] for k in base.edge_vars.keys()}
    
    for k, v in assignment.items():
        if k[0] == prefixes[ET.PATH] and v:
            [p_var, demand_id] = k.split("_")
            (source, target, number) = edges[p_var.replace(prefixes[ET.PATH], "")]
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
                
    nx.nx_pydot.write_dot(network, file_path + ".dot") 
    graphs = pydot.graph_from_dot_file(file_path + ".dot")   
    if graphs is not None:
        (graph,) = graphs
        graph.del_node('"\\n"')
        graph.write_png(file_path + ".png")     

def draw_assignment_path_vars(assignment: dict[str, bool], base, paths: list[list], unique_channels, topology: MultiDiGraph, file_path="../assignedGraphs/assignedRSA"):
    def power(var: str, type: ET):
        val = int(var.replace(prefixes[type], ""))
        # Total binary vars - var val (hence l1 => |binary vars|)
        exponent = val - 1 
        
        return 2 ** (exponent)

        
    network = nx.create_empty_copy(topology)
    colors = {str(k):0 for k in base.demand_vars.keys()}
    
    demand_to_chosen_channel = {str(k):0 for k in base.demand_vars.keys()}

    for k, v in assignment.items():
        if k[0] == prefixes[ET.CHANNEL] and v:
            [c_var, demand_id] = k.split("_")
            demand_to_chosen_channel[demand_id] += power(c_var, ET.CHANNEL)
    
    counting_path_number = {str(k): 0 for k in base.demand_vars.keys()}
    
    for k, v in assignment.items():
        if k[0] == prefixes[ET.PATH] and v:
            
            [p_var, demand_id] = k.split("_")
            counting_path_number[demand_id] += power(p_var, ET.PATH)
    
    slots_used_on_edges = {k : [] for k in base.edge_vars.keys()}

    for demand_id in base.demand_vars.keys():
        path = paths[counting_path_number[str(demand_id)]]
        channel_index = demand_to_chosen_channel[str(demand_id)]
            
        for source, target, number in path:
            slots_used_on_edges[(source, target, number)].append(channel_index)    
            channel = unique_channels[channel_index]
            
            network.add_edge(source, target, label=f"[{channel[0]},{channel[-1]}]", color=color_short_hands[int(demand_id)])
        
    edge_colors = nx.get_edge_attributes(network,'color').values()
    
    # nx.draw(network, edge_color=edge_colors, with_labels=True, node_size = 15, font_size=10)
    # plt.savefig("./assignedGraphs/" + "assigned" + ".png", format="png")
    # plt.close()  
    
    nx.nx_pydot.write_dot(network, file_path + ".dot") 
    graphs = pydot.graph_from_dot_file(file_path + ".dot")   
    if graphs is not None:
        (graph,) = graphs
        graph.del_node('"\\n"')
        graph.write_png(file_path + ".png")   

# if __name__ == "__main__":
  
#     G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../../dot_examples/simple_simple_net.dot"))
#     G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../../dot_examples/simple_net.dot"))
#     G = MultiDiGraph(nx.nx_pydot.read_dot("../../dot_examples/four_node.dot"))
#     G = topology.get_nx_graph("../" + topology.TOPZOO_PATH +  "/Ai3.gml")

#     if G.nodes.get("\\n") is not None:
#         G.remove_node("\\n")
        
#     num_of_demands = 5
#     offset = 0
#     seed = 10

#     demands = topology.get_gravity_demands(G, num_of_demands, seed)
#     ordering = [ET.EDGE, ET.CHANNEL, ET.NODE, ET.DEMAND, ET.TARGET, ET.PATH, ET.SOURCE]
#     channels = topology.get_channels(demands, number_of_slots=50)
    
#     sizes = {d : len(cs[0]) for d, cs in channels.items() if len(cs) > 0}
#     print("sizes")
#     #print(sizes)
#     overlapping, unique = topology.get_overlapping_channels(channels)
    
    
#     #rsa = RSAProblem(G, demands, ordering, channels, unique, overlapping, limit=True)
#     rsa = AllRightBuilder(G, demands).encoded_fixed_paths(1).split(True).limited().construct()
#     import time
#     print(demands)
#     for i in range(1,10000): 
#         assignments = rsa.get_assignments(i)
       
#         if len(assignments) < i:
#             break
        
#         draw_assignment_path_vars(assignments[i-1], rsa.result_bdd.base, rsa.get_simple_paths(), 
#                                 rsa.get_unique_channels(), G)
#         # time.sleep(0.01)
        
        

