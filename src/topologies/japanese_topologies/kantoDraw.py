import networkx as nx
import matplotlib.pyplot as plt

# Parse the GML file
filename = "kanto11.gml"
G = nx.read_gml("kanto11.gml")

# Get node population data
node_population = nx.get_node_attributes(G, 'population')

# Normalize population values for better visualization of node sizes
populations = list(node_population.values())
max_population = max(populations)
min_population = min(populations)

# Normalize population values to be between 500 and 3000
normalized_population = {node: 100 + ((population - min_population) / (max_population - min_population)) * 5000
                         for node, population in node_population.items()}

# Draw the graph
plt.figure(figsize=(10, 6))
pos = nx.spring_layout(G)  # Position nodes using the spring layout algorithm
nx.draw(G, pos, with_labels=True, node_size=[normalized_population[node] for node in G.nodes()],
        node_color="skyblue", font_size=10, font_weight="bold")

# Add node IDs and 'dif' attribute beside the nodes
node_labels = nx.get_node_attributes(G, 'label')
node_dif = nx.get_node_attributes(G, 'dif')
for node, label in node_labels.items():
    x, y = pos[node]
    label_text = f"{label}"
    if node_dif.get(node) is not None:
        label_text += f"\nDif: {node_dif[node]}"
    plt.text(x, y, label_text, horizontalalignment='center', verticalalignment='center')

# Save the graph as a PNG file
plt.title("Multigraph of "+ filename + " with Dif and Node Population")
plt.axis("off")
plt.savefig(filename + "_multigraph_with_population_larger.png", format="PNG")
plt.close()
