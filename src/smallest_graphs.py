import os
import networkx as nx
from topology import get_demands
from topology import get_nx_graph
from networkx import digraph
from networkx import MultiDiGraph
import json

def get_data(graphs : list[tuple[str, MultiDiGraph]]):
    data = {}
    for n,g in graphs:
        data[n] = {}
        data[n]["edges"] = g.number_of_edges()
        data[n]["nodes"] = g.number_of_nodes()
        data[n]["density"] = nx.density(g)
    
    return data   
        


graphs = []
for subdirs, dirs, files in os.walk("./topologies/topzoo"):
    for f in files:
        G = get_nx_graph(subdirs+"/"+f)
        if G.nodes.get("\\n") is not None:
            G.remove_node("\\n")
        graphs.append((f.replace(".gml",""),G))

data = get_data(graphs)


with open("topologies/graph_data.json","w") as f:
    data = json.dump(data, f, indent=4)



#graphs.sort(key=lambda f: f[1])
#graphs = [f + "\n" for (f,size) in graphs][:19]

#with open("topologies/smallest19.txt", "w") as f:
 #   f.writelines(graphs)