import networkx as nx
from pathlib import Path
import matplotlib.pyplot as plt
import os

TOPZOO_PATH = ".\\topologies\\topzoo"

def get_nx_graph(name):
    return nx.DiGraph(nx.read_gml(str(Path(name).resolve()), label='id'))
    

def get_all_graphs():
    all_graphs = []
    names = get_all_topzoo_files()
    for name in names : 
        g = get_nx_graph(name)
        all_graphs.append(g)
    return all_graphs
    
def get_all_topzoo_files():
    topfiles = []
    # Not connected graphs  
    bad = {"BtLatinAmerica.gml","Eunetworks.gml", "Padi.gml","UsSignal.gml",
            "Oteglobe.gml","Ntt.gml","Ntelos.gml","KentmanApr2007.gml","Tw.gml",
            "DialtelecomCz.gml","KentmanAug2005.gml","Nsfcnet.gml","Telcove.gml","Bandcon.gml",
            "JanetExternal.gml","Zamren.gml","DeutscheTelekom.gml","Nordu2010.gml","Easynet.gml"} 

    skip = {TOPZOO_PATH + "/" + b for b in bad}

    # Get all GML files in TOPZOO_PATH directory
    for entry in os.scandir(TOPZOO_PATH):
        if entry.path.endswith(".gml") and entry.is_file() and entry.path not in skip:
            topfiles.append(entry.path)
    return topfiles

def draw_graph(graph, file_name): 
    nx.draw(graph, with_labels=True, node_size = 15, font_size=10)
    plt.savefig("./drawnGraphs/" + file_name + ".svg", format="svg")
    plt.close()

def main():
    all_graphs = get_all_graphs()
    for g in all_graphs : 
        draw_graph(g, g.graph["label"])
        print(g.graph["label"])


if __name__ == "__main__":
    main()