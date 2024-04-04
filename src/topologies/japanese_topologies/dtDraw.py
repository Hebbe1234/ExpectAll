import networkx as nx
import matplotlib.pyplot as plt

# Load the graph from the .gml file
G = nx.read_gml("dt.gml")

# Extract node populations
populations = {node: data["population"] for node, data in G.nodes(data=True)}

# Scale node sizes based on populations
node_sizes = [populations[node] / 1000 for node in G.nodes()]

# Draw the graph
pos = nx.spring_layout(G)  # or any other layout you prefer
nx.draw(G, pos, with_labels=True, node_size=node_sizes, cmap=plt.cm.Blues, font_size=8, font_weight='bold')

# Save the graph as a PNG image
plt.savefig("dt.png", format="PNG")
