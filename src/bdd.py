
from enum import Enum
from dd.autoref import BDD as _BDD
import networkx as nx
from networkx import digraph
import math

def print_bdd(bdd: _BDD, expr, filename="network.svg"):
    bdd.dump(f"../out/{filename}", roots=[expr])
    
def get_assignments(bdd: _BDD, expr):
    print(list(bdd.pick_iter(expr)))


class BDD: 
    
    class ET(Enum):
        VARIABLE=1
        EDGE=2
        DEMAND=3
        LAMBDA=4

    prefixes = {
        ET.VARIABLE: "v",
        ET.EDGE: "e",
        ET.DEMAND: "d",
        ET.LAMBDA: "l",
    }
    
    def __init__(self, topology: digraph.DiGraph):
        self.bdd = _BDD()
        self.variables = []
        self.node_vars = {str(v):i for i,v in enumerate(topology.nodes)}
        self.edge_vars = {str(e):i for i,e in enumerate(topology.edges)}

        self.gen_vars()
    
    def gen_vars(self):
        variable_encoding_count = math.ceil(math.log2(len(self.node_vars.keys())))
        edge_encoding_count = math.ceil(math.log2(len(self.edge_vars.keys())))
        
        v_bdd_vars = [f"{BDD.prefixes[BDD.ET.VARIABLE]}{variable_encoding_count - i }" for i in range(0,variable_encoding_count)] 
        e_bdd_vars = [f"{BDD.prefixes[BDD.ET.EDGE]}{variable_encoding_count - i }" for i in range(0,edge_encoding_count)] 
        self.bdd.declare(*v_bdd_vars)
        self.bdd.declare(*e_bdd_vars)
        
    
    def compile(self):
        return self.bdd
    
    def get_index(self, item, type: ET) -> int:
        if type == BDD.ET.VARIABLE:
            return self.node_vars[str(item)]
        
        if type == BDD.ET.EDGE:
            return self.edge_vars[str(item)]
        
        return 0
    
    def binary_encode(self, type: ET, number: int):
        encoding_count = 0
        match type:
            case BDD.ET.VARIABLE: encoding_count = math.ceil(math.log2(len(self.node_vars.keys())))
            case BDD.ET.EDGE: encoding_count = math.ceil(math.log2(len(self.edge_vars.keys())))
            case BDD.ET.DEMAND: encoding_count = 0
            case BDD.ET.LAMBDA: encoding_count = 0
            case _: encoding_count = 0
        
        encoding_expr = self.bdd.true
        for j in range(encoding_count):
            v = self.bdd.var(f"{BDD.prefixes[type]}{j+1}")
            if not (number >> (encoding_count - 1 - j)) & 1:
                v = ~v
            
            encoding_expr = encoding_expr & v
        
        return encoding_expr
 

class InBDD():
    
    def __init__(self, topology: digraph.DiGraph, base: BDD):
        self.base = base
        in_edges = [(v, topology.in_edges(v)) for v in topology.nodes]
        
        self.in_expr = self.base.bdd.false
        
        for (v, edges) in in_edges:
            print((v,edges))
            for e in edges:
                v_enc = base.binary_encode(BDD.ET.VARIABLE, base.get_index(v, BDD.ET.VARIABLE))
                e_enc = base.binary_encode(BDD.ET.EDGE, base.get_index(e, BDD.ET.EDGE))
                
                self.in_expr = self.in_expr | (v_enc & e_enc)
    
class OutBDD():
    def __init__(self, topology: digraph.DiGraph, base: BDD):
        self.base = base
        out_edges = [(v, topology.out_edges(v)) for v in topology.nodes]
        
        self.out_expr = self.base.bdd.false
        
        for (v, edges) in out_edges:
            print((v,edges))
            for e in edges:
                v_enc = base.binary_encode(BDD.ET.VARIABLE, base.get_index(v, BDD.ET.VARIABLE))
                e_enc = base.binary_encode(BDD.ET.EDGE, base.get_index(e, BDD.ET.EDGE))
                
                self.out_expr = self.out_expr | (v_enc & e_enc)

if __name__ == "__main__":
    G = nx.DiGraph(nx.nx_pydot.read_dot("../dot_examples/simple_net.dot"))

    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
    
    base = BDD(G)
    
    in_expr = InBDD(G, base)
    out_expr = OutBDD(G, base)
    
    print([f"{'' if (1 >> j) & 1 else '~'}e{j+1}" for j in range(2)  ])

    
