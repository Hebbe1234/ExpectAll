import networkx as nx
from topology import get_demands
from topology import get_nx_graph
from topology import draw_graph
from networkx import digraph
from networkx import MultiDiGraph
import pickle


graphs = ["Nsfcnet.gml",
"Istar.gml",
"Nordu1989.gml",
"TLex.gml",
"KentmanJan2011.gml",
"Fccn.gml",
"Zamren.gml",
"Cudi.gml",
"GtsRomania.gml",
"Ulaknet.gml"]

max_wavelengths = 10

for g in graphs:
    G = get_nx_graph("./topologies/topzoo/"+g)
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    for n1 in G.nodes(data=False):
        for n2 in G.nodes(data=False):
            num_edges = G.number_of_edges(n1,n2)
            num_edges2 = G.number_of_edges(n2,n1)

            print(num_edges, num_edges2)
    continue
    for n1 in G.nodes(data=False):
        for n2 in G.nodes(data=False):
            num_edges = G.number_of_edges(n1,n2)
            if num_edges == 0 or num_edges >= max_wavelengths:
                continue
            
            for i in range(max_wavelengths - num_edges):
                G.add_edge(n1,n2)



    #nx.write_gml(G, "./topologies/topzoosynth_for_wavelengths/"+g)
    #draw_graph(G, g + "_synth")



