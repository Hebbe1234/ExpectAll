
from enum import Enum
from dd.autoref import BDD as _BDD
from dd.autoref import Function
import networkx as nx
from networkx import digraph
import math
import itertools

def print_bdd(bdd: _BDD, expr, filename="network.svg"):
    bdd.dump(f"../out/{filename}", roots=[expr])
    
def get_assignments(bdd: _BDD, expr):
    return list(bdd.pick_iter(expr))
    
def get_assignments_block(bdd: _BDD, block):
    return get_assignments(bdd, block.expr)
    

class Demand:
    def __init__(self, source: str, target: str):  
        self.source = source 
        self.target = target
    

class BDD: 
    
    class ET(Enum):
        NODE=1
        EDGE=2
        DEMAND=3
        LAMBDA=4
        PATH=5
        SOURCE=6
        TARGET=7

    prefixes = {
        ET.NODE: "v",
        ET.EDGE: "e",
        ET.DEMAND: "d",
        ET.LAMBDA: "l",
        ET.PATH: "p",
        ET.SOURCE: "s", 
        ET.TARGET: "t", 

    }
    
    
    
    def __init__(self, topology: digraph.DiGraph, demands: dict[int, Demand]):
        self.bdd = _BDD()
        self.variables = []
        self.node_vars = {str(v):i for i,v in enumerate(topology.nodes)}
        self.edge_vars = {str(e):i for i,e in enumerate(topology.edges)} #TODO This might not work with multigraphs as str(e) would be the same for all edges between the same nodes 
        self.demand_vars = demands
        self.encoded_node_vars :list[str]= []
        self.encoded_source_vars :list[str]= []
        self.encoded_target_vars :list[str]= []
        self.gen_vars()
    
    def gen_vars(self):
        variable_encoding_count = math.ceil(math.log2(len(self.node_vars.keys())))
        v_bdd_vars = [f"{BDD.prefixes[BDD.ET.NODE]}{variable_encoding_count - i }" for i in range(0,variable_encoding_count)] 
        self.bdd.declare(*v_bdd_vars)

        self.encoded_node_vars = v_bdd_vars

        s_bdd_vars = [f"{BDD.prefixes[BDD.ET.SOURCE]}{variable_encoding_count - i }" for i in range(0,variable_encoding_count)] 
        self.bdd.declare(*s_bdd_vars)
        self.encoded_source_vars = s_bdd_vars

        t_bdd_vars = [f"{BDD.prefixes[BDD.ET.TARGET]}{variable_encoding_count - i }" for i in range(0,variable_encoding_count)] 
        self.bdd.declare(*t_bdd_vars)
        self.encoded_target_vars = t_bdd_vars

        edge_encoding_count = math.ceil(math.log2(len(self.edge_vars.keys())))
        e_bdd_vars = [f"{BDD.prefixes[BDD.ET.EDGE]}{edge_encoding_count - i }" for i in range(0,edge_encoding_count)] 
        self.bdd.declare(*e_bdd_vars)
        
        demand_encoding_count = math.ceil(math.log2(len(self.demand_vars.keys())))
        d_bdd_vars = [f"{BDD.prefixes[BDD.ET.DEMAND]}{demand_encoding_count - i}" for i in range(0,demand_encoding_count)] 
        self.bdd.declare(*d_bdd_vars)
        
        p_bdd_vars = []
        for edge in self.edge_vars.values():
            for demand in self.demand_vars.keys():
                p_bdd_vars.append(f"{BDD.prefixes[BDD.ET.PATH]}{edge}_{demand}")

        for edge in self.edge_vars.values():
            p_bdd_vars.append(f"{BDD.prefixes[BDD.ET.PATH]}{edge}")
        
        self.bdd.declare(*p_bdd_vars)

    def make_subst_mapping(self, l1: list[str], l2: list[str]):
        return {l1_e: l2_e for (l1_e, l2_e) in zip(l1, l2)}
    
    def get_p_var(self, edge: int, demand: (int|None) = None):
        return f"{BDD.prefixes[BDD.ET.PATH]}{edge}{f'_{demand}' if demand is not None else ''}"

    def get_p_vector(self, demand: int):
        return {self.get_p_var(edge): self.get_p_var(edge, demand) for edge in self.edge_vars.values()}
        
    def compile(self):
        return self.bdd
    
    def get_index(self, item, type: ET):
        if type == BDD.ET.NODE:
            return self.node_vars[str(item)]
        
        if type == BDD.ET.EDGE:
            return self.edge_vars[str(item)]
        
        if type == BDD.ET.DEMAND:
            assert isinstance(item, int)
            return item
        
        return 0
    
    def equals(self, e1: list[str], e2: list[str]):
        assert len(e1) == len(e2)

        expr = self.bdd.true
        for (var1, var2) in zip(e1,e2):
            s = (self.bdd.var(var1) & self.bdd.var(var2)) | (~self.bdd.var(var1) & ~self.bdd.var(var2))
            expr = expr & s

        return expr
    
    def binary_encode(self, type: ET, number: int):
        encoding_count = 0
        match type:
            case BDD.ET.NODE: encoding_count = math.ceil(math.log2(len(self.node_vars.keys())))
            case BDD.ET.EDGE: encoding_count = math.ceil(math.log2(len(self.edge_vars.keys())))
            case BDD.ET.DEMAND: encoding_count = math.ceil(math.log2(len(self.demand_vars.keys())))
            case BDD.ET.LAMBDA: encoding_count = 0
            case _: encoding_count = 0
        
        encoding_expr = self.bdd.true
        for j in range(encoding_count):
            v = self.bdd.var(f"{BDD.prefixes[type]}{j+1}")
            if not (number >> (encoding_count - 1 - j)) & 1:
                v = ~v
            
            encoding_expr = encoding_expr & v
          
        return encoding_expr
    
    def binary_encode_as_list_of_variables(self, type: ET, number: int):
        encoding_count = 0
        match type:
            case BDD.ET.NODE: encoding_count = math.ceil(math.log2(len(self.node_vars.keys())))
            case BDD.ET.EDGE: encoding_count = math.ceil(math.log2(len(self.edge_vars.keys())))
            case BDD.ET.DEMAND: encoding_count = math.ceil(math.log2(len(self.demand_vars.keys())))
            case BDD.ET.LAMBDA: encoding_count = 0
            case _: encoding_count = 0

        variables :list[Function]= []        
        for j in range(encoding_count):
            v = self.bdd.var(f"{BDD.prefixes[type]}{j+1}")
            if not (number >> (encoding_count - 1 - j)) & 1:
                v = ~v
            variables.append(v)
        
        return variables
 
class Block:
    def __init__(self, base: BDD):
        self.expr = base.bdd.true
        pass

class TrivialBlock(Block): 
    def __init__(self, topology: digraph.DiGraph, demand: Demand,  base: BDD):
        self.expr = base.bdd.true 
        s_encoded = base.binary_encode_as_list_of_variables(BDD.ET.NODE, base.get_index(demand.source, BDD.ET.NODE))
        t_encoded = base.binary_encode_as_list_of_variables(BDD.ET.NODE, base.get_index(demand.target, BDD.ET.NODE))
        #print(base.make_subst_mapping(base.encoded_node_vars, base.encoded_target_vars))




        s_subst_expr = base.bdd.let(base.make_subst_mapping(base.encoded_node_vars, base.encoded_source_vars), s_encoded)
        t_subst_expr = base.bdd.let(base.make_subst_mapping(base.encoded_node_vars, base.encoded_target_vars), t_encoded)

        #print(s_subst_expr)



        # self.expr = self.expr & (s_subst_expr.equiv(t_subst_expr))


#WOrks
        # for e in topology.edges(): 
        #     p_var :str = base.get_p_var(base.get_index(e, BDD.ET.EDGE)) 
        #     self.expr = self.expr & (~base.bdd.var(p_var))
        
       

class InBlock(Block):
    def __init__(self, topology: digraph.DiGraph, base: BDD):
        self.expr = base.bdd.false
        in_edges = [(v, topology.in_edges(v)) for v in topology.nodes]
        for (v, edges) in in_edges:
            for e in edges:
                v_enc = base.binary_encode(BDD.ET.NODE, base.get_index(v, BDD.ET.NODE))
                e_enc = base.binary_encode(BDD.ET.EDGE, base.get_index(e, BDD.ET.EDGE))
                
                self.expr = self.expr | (v_enc & e_enc)
    
class OutBlock(Block):
    def __init__(self, topology: digraph.DiGraph, base: BDD):
        out_edges = [(v, topology.out_edges(v)) for v in topology.nodes]        
        self.expr = base.bdd.false
        
        for (v, edges) in out_edges:
            for e in edges:
                v_enc = base.binary_encode(BDD.ET.NODE, base.get_index(v, BDD.ET.NODE))
                e_enc = base.binary_encode(BDD.ET.EDGE, base.get_index(e, BDD.ET.EDGE))
                
                self.expr = self.expr | (v_enc & e_enc)

class SourceBlock(Block):
    def __init__(self, demands: dict[int, Demand], base: BDD):
        self.expr = base.bdd.false
        
        for i, demand in demands.items():
            v_enc = base.binary_encode(BDD.ET.NODE, base.get_index(demand.source, BDD.ET.NODE))
            d_enc = base.binary_encode(BDD.ET.DEMAND, base.get_index(i, BDD.ET.DEMAND))
            self.expr = self.expr | (v_enc & d_enc)

class TargetBlock(Block):
    def __init__(self, demands: dict[int, Demand], base: BDD):
        self.expr = base.bdd.false
        
        for i, demand in demands.items():
            v_enc = base.binary_encode(BDD.ET.NODE, base.get_index(demand.target, BDD.ET.NODE))
            d_enc = base.binary_encode(BDD.ET.DEMAND, base.get_index(i, BDD.ET.DEMAND))
            self.expr = self.expr | (v_enc & d_enc)
        
             
        
if __name__ == "__main__":
    G = nx.DiGraph(nx.nx_pydot.read_dot("../dot_examples/simple_net.dot"))
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
    
    demands = {0: Demand("A", "B"),1: Demand("B", "C")}
    base = BDD(G, demands)
    
    in_expr = InBlock(G, base)
    out_expr = OutBlock(G, base)
    source_expr = SourceBlock(demands, base)
    target_expr = TargetBlock(demands, base)
    trivial_expr = TrivialBlock(G,demands[1], base)

    print(get_assignments_block(base.bdd, trivial_expr))