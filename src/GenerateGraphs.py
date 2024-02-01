from graphviz import Digraph

def generate_chain_graph(length, startSymbol):
    if length < 1:
        raise ValueError("Chain length must be at least 1.")

    graph = Digraph('G')
    
    # Create nodes and edges for the chain
    for i in range(length - 1):
        node_from = startSymbol+str(i)# A, B, C, ...
        node_to = startSymbol+str(i+1)  # B, C, D, ...

        graph.edge(node_from, node_to)

    return graph

def save_to_txt(graph_source, filename):
    with open(filename, 'w') as file:
        file.write(graph_source)

if __name__ == "__main__":
    chain_length = int(input("Enter the chain length: "))
    
    try:
        chain_graph = generate_chain_graph(chain_length, 'n')
        graph_source = chain_graph.source
        print(graph_source)

        txt_filename = input("Enter the filename to save the graph (without extension): ")
        txt_filename += ".txt"

        save_to_txt(graph_source, txt_filename)
        print(f"Graph saved as {txt_filename} successfully!")
    except ValueError as e:
        print(f"Error: {e}")
