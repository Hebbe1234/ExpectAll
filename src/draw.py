from networkx import MultiDiGraph
from demands import Demand
import networkx as nx
import topology
from bdd_edge_encoding import BDD, RWAProblem
import matplotlib.pyplot as plt
import pydot

def draw_assignment(assignment: dict[str, bool], base: BDD, topology:MultiDiGraph):
    def power(l_var: str):
        val = int(l_var.replace(base.prefixes[BDD.ET.LAMBDA], ""))
        # Total binary vars - var val (hence l1 => |binary vars|)
        exponent = base.encoding_counts[BDD.ET.LAMBDA] - val
        
        return 2 ** (exponent)
        
    network = nx.create_empty_copy(topology)
    colors = {str(k):0 for k in base.demand_vars.keys()}
    
    for k, v in assignment.items():
        if k[0] == base.prefixes[BDD.ET.LAMBDA] and v:
                
            [l_var, demand_id] = k.split("_")
            colors[demand_id] += power(l_var)
    
    print(colors)
    
    edges = {str(v) : k for k , v in base.edge_vars.items()}
    
    for k, v in assignment.items():
        if k[0] == base.prefixes[BDD.ET.PATH] and v:
            [p_var, demand_id] = k.split("_")
            (source, target, number) = edges[p_var.replace(base.prefixes[BDD.ET.PATH], "")]
            network.add_edge(source, target, label=demand_id, color=color_map[colors[demand_id]])
        
    edge_colors = nx.get_edge_attributes(network,'color').values()
    
    # nx.draw(network, edge_color=edge_colors, with_labels=True, node_size = 15, font_size=10)
    # plt.savefig("./assignedGraphs/" + "assigned" + ".png", format="png")
    # plt.close()  
    
    nx.nx_pydot.write_dot(network, "./assignedGraphs/" + "assigned" + ".dot") 
    graphs = pydot.graph_from_dot_file("./assignedGraphs/" + "assigned" + ".dot")   
    if graphs is not None:
        (graph,) = graphs
        graph.write_png("./assignedGraphs/" + "assigned" + ".png")     


def draw_assignment_p_encoding(assignment: dict[str, bool], base: BDD, topology:MultiDiGraph):
    def power(l_var: str):
        val = int(l_var.replace(base.prefixes[BDD.ET.LAMBDA], ""))
        # Total binary vars - var val (hence l1 => |binary vars|)
        exponent = base.encoding_counts[BDD.ET.LAMBDA] - val
        
        return 2 ** (exponent)
        
    network = nx.create_empty_copy(topology)

    demands_on_edges = {str(id): {  } for e_object, id in base.edge_vars.items()}
#str(w):-1 for w in range(base.wavelengths)

    
    for k, v in assignment.items():
        if k[0] == base.prefixes[BDD.ET.PATH] and v:
          #  print(k)
            [_, edge, demand_and_wavelength] = k.split("_")
            [demand_bit, wavelength] = demand_and_wavelength.split("^")
            if wavelength in demands_on_edges[edge].keys() : 
                demands_on_edges[edge][wavelength] += 2 ** (base.encoding_counts[BDD.ET.DEMAND]-int(demand_bit))
            else : 
                demands_on_edges[edge][wavelength] = 2 ** (base.encoding_counts[BDD.ET.DEMAND]-int(demand_bit))

    edges = {str(v) : k for k , v in base.edge_vars.items()}
    flag = False 
    for edge, lambd_demand_dict in demands_on_edges.items() :
        for lambd, demand in lambd_demand_dict.items(): 

            (source, target, number) = edges[edge]
            network.add_edge(source, target, label="d"+str(demand)+" e"+str(edge), color=color_map[int(lambd)])
 
        # if len(k) != len(set(k)):
        #     print("DET FJLEDE")
        #     print(k)

        #     if 1 in k : 
        #         flag = True

    
    
    # for k, v in assignment.items():
    #     if k[0] == base.prefixes[BDD.ET.PATH] and v:
    #         [p_var, demand_id] = k.split("_")
    #         (source, target, number) = edges[p_var.replace(base.prefixes[BDD.ET.PATH], "")]
    #         network.add_edge(source, target, label=demand_id, color=color_map[colors[demand_id]])
        
    edge_colors = nx.get_edge_attributes(network,'color').values()
    
    # nx.draw(network, edge_color=edge_colors, with_labels=True, node_size = 15, font_size=10)
    # plt.savefig("./assignedGraphs/" + "assigned" + ".png", format="png")
    # plt.close()  
    
    nx.nx_pydot.write_dot(network, "./assignedGraphs/" + "assigned" + ".dot") 
    graphs = pydot.graph_from_dot_file("./assignedGraphs/" + "assigned" + ".dot")   
    if graphs is not None:
        (graph,) = graphs
        graph.write_png("./assignedGraphs/" + "assigned" + ".png")     
    if flag : 
        exit()

import random
if __name__ == "__main__":
    color_short_hands = ['red', 'blue', 'green', 'yellow', 'brown', 'black', 'purple', 'lightcyan', 'lightgreen', 'pink', 'lightsalmon', 'lime', 'khaki', 'moccasin', 'olive', 'plum', 'peru', 'tan', 'tan2', 'khaki4', 'indigo']
    color_map = {i : color_short_hands[i] for i in range(len(color_short_hands))}
    
    G = topology.get_nx_graph(topology.TOPZOO_PATH +  "/AI3.gml")
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/simple_simple_net.dot"))
    G = MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/four_node.dot"))

    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
        
    demands = {0: Demand("A", "A")}
    num_of_demands = 4
    offset = 1
    seed = 2
    # demands = topology.get_demands(G, amount=5, seed=random.randint(0,100))
    demands = topology.get_demands(G, num_of_demands, offset, seed)
    # types = [BDD.ET.LAMBDA, BDD.ET.DEMAND,  BDD.ET.EDGE, BDD.ET.SOURCE, BDD.ET.TARGET, BDD.ET.NODE, BDD.ET.PATH]
    types_p_edge_encoding = [BDD.ET.EDGE, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH,BDD.ET.SOURCE]

    # rwa = RWAProblem(G, demands, wavelengths=5, ordering=types)
    rw1 = RWAProblem(G, demands, types_p_edge_encoding, wavelengths=4, group_by_edge_order =True, generics_first=False, binary=True)
    import time

    print(demands)
    for i in range(1,100): 
        assignment = rw1.get_assignments(i)[i-1]
        draw_assignment_p_encoding(assignment, rw1.base, G)
        time.sleep(0.1)

