import argparse
import math
from bdd import RWAProblem, BDD
from topology import get_demands
from topology import get_nx_graph
from dd.autoref import BDD as _BDD
import re
from itertools import permutations, chain, combinations,combinations_with_replacement
def list_to_dict(c):
    return {var: level for level, var in enumerate(c)}

def powerset(iterable):
    s = list(iterable)  # allows duplicate elements
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))


if __name__ == "__main__":
	
    parser = argparse.ArgumentParser("mainreordering.py")
    parser.add_argument("--filename", type=str, help="file to run on")
    parser.add_argument("--wavelengths", default=5, type=int, help="number of wavelengths")
    parser.add_argument("--demands", default=5, type=int, help="number of demands")
    args = parser.parse_args()

    G = get_nx_graph("./topologies/topzoo/"+args.filename)
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    demands = get_demands(G, args.demands)
    
    types = [BDD.ET.LAMBDA, BDD.ET.DEMAND, BDD.ET.PATH, BDD.ET.EDGE, BDD.ET.SOURCE, BDD.ET.TARGET, BDD.ET.NODE]


    forced_order = [BDD.ET.EDGE]
    ordering = [t for t in types if t not in forced_order]
    
    for b1 in [True, False]:
        for b2 in [True, False]:       
            print("Building RWA Problem: ")
            rwa = RWAProblem(G, demands, forced_order+[*ordering], args.wavelengths, other_order =b1, generics_first=b2, with_sequence=False)
            bdd = rwa.base.bdd
            print("")
            
            prefixes_to_vars = {}
            for v in bdd.vars:
                prefix = re.sub(r"\d", "|", str(v)).split("|")[0]
                if prefix not in prefixes_to_vars:
                    prefixes_to_vars[prefix] = []
                    
                prefixes_to_vars[prefix].append(v)
            
            singles = [p for p in prefixes_to_vars if len(p) == 1]
            has_multiple = [p for p in prefixes_to_vars if p + p in prefixes_to_vars]
            
            t_perms = permutations(singles)
            
            min_t_p = None
            min_m_p = None
            min_len = math.inf
            
            for i, t_p in enumerate(t_perms):
                mult_perms = powerset(has_multiple)

                for j, m_p in enumerate(mult_perms):
                    new_order = []

                    for t in list(t_p):
                        if t in m_p:
                            for elem in prefixes_to_vars[t]:
                                new_order.extend([elem, t + elem])
                        else:
                            for elem in prefixes_to_vars[t]:
                                new_order.append(elem)
                            
                            if t in has_multiple:
                                for elem in prefixes_to_vars[t+t]:
                                    new_order.append(elem)
                
                    bdd.reorder(list_to_dict(new_order))
                    
                    print(f"{i}_{j}; {b1}; {b2}; {t_p}; {m_p}; {len(bdd)}")
                    
                    if len(bdd) < min_len:
                        min_t_p = t_p
                        min_m_p = m_p
                        min_len = len(bdd)
                    

            print(min_len)
            print(min_t_p)
        
    