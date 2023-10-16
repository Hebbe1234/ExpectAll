
from enum import Enum
from dd.autoref import BDD as _BDD
from dd.autoref import Function
import networkx as nx
from networkx import digraph
from networkx import MultiDiGraph
import math
from demands import Demand

def print_bdd(bdd: _BDD, expr, filename="network.svg"):
    bdd.dump(f"../out/{filename}", roots=[expr])

def get_assignments(bdd: _BDD, expr):
    return list(bdd.pick_iter(expr))

def get_assignments_block(bdd: _BDD, block):
    return get_assignments(bdd, block.expr)



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

    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand], wavelengths: int = 2):
        self.bdd = _BDD()
        self.variables = []
        self.node_vars = {str(v):i for i,v in enumerate(topology.nodes)}
        self.edge_vars = {str(e):i for i,e in enumerate(topology.edges)} #TODO This might not work with multigraphs as str(e) would be the same for all edges between the same nodes
        self.demand_vars = demands
        self.encoded_node_vars :list[str]= []
        self.encoded_source_vars :list[str]= []
        self.encoded_target_vars :list[str]= []
        self.wavelengths = wavelengths
        
        self.encoding_counts = {
            BDD.ET.NODE: math.ceil(math.log2(len(self.node_vars.keys()))),
            BDD.ET.EDGE:  math.ceil(math.log2(len(self.edge_vars.keys()))),
            BDD.ET.DEMAND:  math.ceil(math.log2(len(self.demand_vars.keys()))),
            BDD.ET.PATH: len(self.edge_vars.keys()),
            BDD.ET.LAMBDA: max(1, math.ceil(math.log2(wavelengths)))
        }
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

        
        ee_bdd_vars = [f"{self.get_prefix_multiple(BDD.ET.EDGE, 2)}{self.encoding_counts[BDD.ET.EDGE]  - i }" for i in range(0,self.encoding_counts[BDD.ET.EDGE] )]
        self.bdd.declare(*ee_bdd_vars)

        dd_bdd_vars = [f"{BDD.prefixes[BDD.ET.DEMAND]}{self.encoding_counts[BDD.ET.DEMAND] - i}" for i in range(0,self.encoding_counts[BDD.ET.DEMAND])]
        self.bdd.declare(*dd_bdd_vars)

        d_bdd_vars = [f"{self.get_prefix_multiple(BDD.ET.DEMAND, 2)}{self.encoding_counts[BDD.ET.DEMAND] - i}" for i in range(0,self.encoding_counts[BDD.ET.DEMAND])]
        self.bdd.declare(*d_bdd_vars)

        self.declare_generic_and_specific_variables(BDD.ET.PATH, list(self.edge_vars.values()))
        self.declare_generic_and_specific_variables(BDD.ET.LAMBDA,  list(range(1, 1 + self.encoding_counts[BDD.ET.LAMBDA])))

        
        demand_encoding_count = math.ceil(math.log2(len(self.demand_vars.keys())))
        d_bdd_vars = [f"{BDD.prefixes[BDD.ET.DEMAND]}{demand_encoding_count - i}" for i in range(0,demand_encoding_count)] 
        self.bdd.declare(*d_bdd_vars)
        
        p_bdd_vars = []
        for edge in self.edge_vars.values():
            for demand in self.demand_vars.keys():
                p_bdd_vars.append(f"{BDD.prefixes[BDD.ET.PATH]}{edge}_{demand}")

    def declare_generic_and_specific_variables(self, type: ET, l: list[int]):
        bdd_vars = []
        for item in l:
            for demand in self.demand_vars.keys():
                bdd_vars.append(f"{BDD.prefixes[type]}{item}_{demand}")

        for item in l:
            bdd_vars.append(f"{BDD.prefixes[type]}{item}")
            bdd_vars.append(f"{self.get_prefix_multiple(type,2)}{item}")

        self.bdd.declare(*bdd_vars)


    def make_subst_mapping(self, l1: list[str], l2: list[str]):
        return {l1_e: l2_e for (l1_e, l2_e) in zip(l1, l2)}
    
    def get_p_var(self, edge: int, demand: (int|None) = None):
        return f"{BDD.prefixes[BDD.ET.PATH]}{edge}{f'_{demand}' if demand is not None else ''}"

    def get_p_vector(self, demand: int):
        l1 = []
        l2 = []
        for edge in  self.edge_vars.values():
            l1.append(self.get_p_var(edge))
            l2.append(self.get_p_var(edge, demand))

        return self.make_subst_mapping(l1, l2)

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
    
    

    def binary_encode(self, type: ET, number: int):
        encoding_count = self.encoding_counts[type]
        encoding_expr = self.bdd.true
        for j in range(encoding_count):
            v = self.bdd.var(f"{BDD.prefixes[type]}{j+1}")
            if not (number >> (encoding_count - 1 - j)) & 1:
                v = ~v

            encoding_expr = encoding_expr & v
          
        return encoding_expr
    
    def binary_encode_as_list_of_variables(self, type: ET, number: int):
        encoding_count = self.encoding_counts[type]

        variables :list[Function]= []        
        for j in range(encoding_count):
            v = self.bdd.var(f"{BDD.prefixes[type]}{j+1}")
            if not (number >> (encoding_count - 1 - j)) & 1:
                v = ~v
            variables.append(v)
        
        return variables


    def get_prefix_multiple(self, type: ET, multiple: int):
        return "".join([BDD.prefixes[type] for _ in range(multiple)])

    def get_encoding_var_list(self, type: ET, override_prefix: (str|None) = None):
        offset = 0
        if type == BDD.ET.PATH:
            offset = 1

        return [f"{BDD.prefixes[type] if override_prefix is None else override_prefix}{i+1 - offset}" for i in range(self.encoding_counts[type])]

    def equals(self, e1: list[str], e2: list[str]):
        assert len(e1) == len(e2)

        expr = self.bdd.true
        for (var1, var2) in zip(e1,e2):
            s = (self.bdd.var(var1) & self.bdd.var(var2)) |(~self.bdd.var(var1) & ~self.bdd.var(var2))
            expr = expr & s

        return expr

class Block:
    def __init__(self, base: BDD):
        self.expr = base.bdd.true

class TrivialBlock(Block): 
    def __init__(self, topology: digraph.DiGraph, demand: Demand,  base: BDD):
        self.expr = base.bdd.true 
        s_encoded :list[str]= base.get_encoding_var_list(BDD.ET.NODE, base.prefixes[BDD.ET.SOURCE])
        t_encoded :list[str]= base.get_encoding_var_list(BDD.ET.NODE, base.prefixes[BDD.ET.TARGET])

        self.expr = self.expr & base.equals(s_encoded, t_encoded)

        for e in topology.edges(): 
            p_var :str = base.get_p_var(base.get_index(e, BDD.ET.EDGE)) 
            self.expr = self.expr & (~base.bdd.var(p_var))
        

       

class InBlock(Block):
    def __init__(self, topology: MultiDiGraph, base: BDD):
        self.expr = base.bdd.false
        in_edges = [(v, topology.in_edges(v)) for v in topology.nodes]
        for (v, edges) in in_edges:
            for e in edges:
                v_enc = base.binary_encode(BDD.ET.NODE, base.get_index(v, BDD.ET.NODE))
                e_enc = base.binary_encode(BDD.ET.EDGE, base.get_index(e, BDD.ET.EDGE))

                self.expr = self.expr | (v_enc & e_enc)

class OutBlock(Block):
    def __init__(self, topology: MultiDiGraph, base: BDD):
        out_edges = [(v, topology.out_edges(v)) for v in topology.nodes]
        self.expr = base.bdd.false

        for (v, edges) in out_edges:
            for e in edges:
                v_enc = base.binary_encode(BDD.ET.NODE, base.get_index(v, BDD.ET.NODE))
                e_enc = base.binary_encode(BDD.ET.EDGE, base.get_index(e, BDD.ET.EDGE))

                self.expr = self.expr | (v_enc & e_enc)

class SourceBlock(Block):
    def __init__(self, base: BDD):
        self.expr = base.bdd.false

        for i, demand in base.demand_vars.items():
            v_enc = base.binary_encode(BDD.ET.NODE, base.get_index(demand.source, BDD.ET.NODE))
            d_enc = base.binary_encode(BDD.ET.DEMAND, base.get_index(i, BDD.ET.DEMAND))
            self.expr = self.expr | (v_enc & d_enc)

class TargetBlock(Block):
    def __init__(self, base: BDD):
        self.expr = base.bdd.false

        for i, demand in base.demand_vars.items():
            v_enc = base.binary_encode(BDD.ET.NODE, base.get_index(demand.target, BDD.ET.NODE))
            d_enc = base.binary_encode(BDD.ET.DEMAND, base.get_index(i, BDD.ET.DEMAND))
            self.expr = self.expr | (v_enc & d_enc)

class PassesBlock(Block):
    def __init__(self, topology: MultiDiGraph, base: BDD):
        self.expr = base.bdd.false
        for edge in topology.edges():
            e_enc = base.binary_encode(BDD.ET.EDGE, base.get_index(edge, BDD.ET.EDGE))
            p_var = base.bdd.var(base.get_p_var(base.get_index(edge, BDD.ET.EDGE)))
            self.expr = self.expr | (e_enc & p_var)

class SingleInBlock(Block):
    def __init__(self, in_b: InBlock, passes: PassesBlock, base:BDD):
        self.expr = base.bdd.true

        e_list = base.get_encoding_var_list(BDD.ET.EDGE)
        ee_list = base.get_encoding_var_list(BDD.ET.EDGE, base.get_prefix_multiple(BDD.ET.EDGE, 2))

        in_1 = in_b.expr
        in_2 = base.bdd.let(base.make_subst_mapping(e_list, ee_list), in_b.expr)

        passes_1 = passes.expr
        passes_2 = base.bdd.let(base.make_subst_mapping(e_list, ee_list), passes.expr)

        equals = base.equals(e_list, ee_list)
        u = in_1 & in_2 & passes_1 & passes_2
        v = u.implies(equals)

        self.expr = base.bdd.forall(e_list + ee_list, v)
        
class SingleOutBlock(Block):
    def __init__(self, out_b: OutBlock, passes: PassesBlock, base:BDD):
        self.expr = base.bdd.true

        e_list = base.get_encoding_var_list(BDD.ET.EDGE)
        ee_list = base.get_encoding_var_list(BDD.ET.EDGE, base.get_prefix_multiple(BDD.ET.EDGE, 2))

        out_1 = out_b.expr
        out_2 = base.bdd.let(base.make_subst_mapping(e_list, ee_list), out_b.expr)

        passes_1 = passes.expr
        passes_2 = base.bdd.let(base.make_subst_mapping(e_list, ee_list), passes.expr)

        equals = base.equals(e_list, ee_list)
        u = out_1 & out_2 & passes_1 & passes_2
        v = u.implies(equals)

        self.expr = base.bdd.forall(e_list + ee_list, v)        

class SingleWavelengthBlock(Block):
    def __init__(self, base: BDD):
        self.expr = base.bdd.false
        for i in range(base.wavelengths):
            self.expr = self.expr | base.binary_encode(BDD.ET.LAMBDA, i)

class NoClashBlock(Block):
    def __init__(self, passes: PassesBlock, base: BDD):
        self.expr = base.bdd.false

        passes_1 = passes.expr
        mappingP = {f"{BDD.prefixes[BDD.ET.PATH]}{i}": f"{base.get_prefix_multiple(BDD.ET.PATH,2)}{i}" for i in range(base.encoding_counts[BDD.ET.PATH])}
        passes_2: Function = passes.expr.let(**mappingP)
        
        l_list = base.get_encoding_var_list(BDD.ET.LAMBDA)
        ll_list =base.get_encoding_var_list(BDD.ET.LAMBDA, base.get_prefix_multiple(BDD.ET.LAMBDA, 2))
        
        d_list = base.get_encoding_var_list(BDD.ET.DEMAND)
        dd_list = base.get_encoding_var_list(BDD.ET.DEMAND, base.get_prefix_multiple(BDD.ET.DEMAND, 2))
        
        e_list = base.get_encoding_var_list(BDD.ET.EDGE)
        
        u = (passes_1 & passes_2).exist(*e_list)
        self.expr = u.implies(~base.equals(l_list, ll_list) | base.equals(d_list, dd_list))
       
if __name__ == "__main__":
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/simple_net.dot"))
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

    demands = {0: Demand("A", "B"),1: Demand("B", "C")}
    base = BDD(G, demands, 1)

    # in_expr = InBlock(G, base)
    # out_expr = OutBlock(G, base)
    # source_expr = SourceBlock(demands, base)
    # target_expr = TargetBlock(demands, base)
    trivial_expr = TrivialBlock(G,demands[1], base)

    # print(get_assignments_block(base.bdd, trivial_expr))
    # source_expr = SourceBlock(base)
    # target_expr = TargetBlock(base)
    # passes_expr = PassesBlock(G, base)
    # singleIn_expr = SingleInBlock(in_expr, passes_expr, base)
    # singleOut_expr = SingleOutBlock(out_expr, passes_expr, base)
    # singleWavelength_expr = SingleWavelengthBlock(base)
    # noClash_expr = NoClashBlock(passes_expr, base)    

    # print(len(get_assignments(base.bdd, trivial_expr.expr)))
  
    # d_list = base.get_encoding_var_list(BDD.ET.DEMAND)
    # dd_list = base.get_encoding_var_list(BDD.ET.DEMAND, base.get_prefix_multiple(BDD.ET.DEMAND, 2))
        
    # u: Function = noClash_expr.expr.forall(*(d_list + dd_list))
    # print(noClash_expr.expr.count())
    # print(u.count())
    
    # x = (noClash_expr.expr & ~base.bdd.var("d1") & base.bdd.var("dd1") & base.bdd.var("l1") & base.bdd.var("ll1"))
    # print((x.exist(*(["d1", "dd1", "l1", "ll1"]))).count())
    # print(get_assignments(base.bdd, u))
    # print(get_assignments(base.bdd, x.exist(*(["d1", "dd1", "l1", "ll1"]))))
  
