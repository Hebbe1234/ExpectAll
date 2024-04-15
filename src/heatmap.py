from demands import Demand
import networkx as nx
import matplotlib.pyplot as plt

def draw_heatmap(G : nx.Graph, paths, savefile = "heatmap.png"):
    edge_occurences = []
    for p in paths:
        edge_occurences.extend(p)

    edge_weights = {e : edge_occurences.count(e) for e in G.edges}
    max_weight = max(edge_weights.values())
    edge_weights = {e : (float(weight)/float(max_weight)) * 10 for e,weight in edge_weights.items()}

    pos = nx.spring_layout(G)  
    arc_rad = 0.15
    nx.draw(G, pos, with_labels=True, connectionstyle=f'arc3, rad = {arc_rad}', width=list(edge_weights.values()), font_size=8, font_weight='bold')

    plt.savefig(savefile, format="PNG")
    

if __name__ == "__main__":
    import topology
    
    G = topology.get_nx_graph("topologies/japanese_topologies/kanto11.gml")
    demands = topology.get_gravity_demands(G,10000, max_uniform=30, multiplier=1)
    paths = topology.get_disjoint_simple_paths(G, demands, 2)  
    savefile = "test.png"
    draw_heatmap(G, paths,savefile)