INF = float('inf')

def find_min_cost_node(N, M, costs):
    min_cost = INF
    min_node = None
    for node in N:
        if node not in M and costs[node] < min_cost:
            min_cost = costs[node]
            min_node = node
    return min_node

def check_spectrum_availability(w, n, Tw, ewn):
    # Assuming Tw is a set representing available spectrum on node w
    # And ewn is a set representing available spectrum on link ewn
    return Tw.intersection(ewn) == ewn

def rsa_algorithm(G, S, D):
    N, E = G
    M = {S}
    CS = {node: (0 if node == S else INF) for node in N}
    TS = {node: set() for node in N}  # Full spectrum initially
    Pi = {node: [S, node] for node in N}
    
    while D not in M:
        w = find_min_cost_node(N, M, CS)
        if not w or CS[w] == INF:
            return "RSA FAIL"
        
        M.add(w)
        for n in N - M:
            if CS[n] > CS[w] + E[(w, n)] and check_spectrum_availability(w, n, TS[w], E[(w, n)]):
                CS[n] = CS[w] + E[(w, n)]
                Pi[n] = Pi[w] + [n]
                TS[n] = TS[w].intersection(E[(w, n)])

    PD = Pi[D]
    TD = TS[D]  # Spectrum assigned to destination D
    return "RSA SUCC", PD, TD

# Example usage
if __name__ == "__main__":
    # Example graph represented as (Node set, Edge set with costs)
    G = ({'S', 'A', 'B', 'C', 'D'}, {('S', 'A'): 1, ('S', 'B'): 3, ('A', 'C'): 2, ('B', 'C'): 4, ('C', 'D'): 3})
    S = 'S'  # Source node
    D = 'D'  # Destination node

    result = rsa_algorithm(G, S, D)
    print(result)
