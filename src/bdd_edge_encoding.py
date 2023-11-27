from enum import Enum

has_cudd = False

try:
    from dd.cudd import BDD as _BDD
    from dd.cudd import Function
    has_cudd = True
except ImportError:
   from dd.autoref import BDD as _BDD
   from dd.autoref import Function 
   print("Using autoref... ")

import networkx as nx
from networkx import digraph
from networkx import MultiDiGraph
import math
from demands import Demand
from itertools import permutations


def print_bdd(bdd: _BDD, expr, filename="network.svg"):
    bdd.dump(f"../out/{filename}", roots=[expr])

def get_assignments(bdd: _BDD, expr):
    return list(bdd.pick_iter(expr))

def get_assignments_block(bdd: _BDD, block):
    return get_assignments(bdd, block.expr)

def pretty_print_block(bdd: _BDD, block):
    ass = get_assignments(bdd, block.expr)
    for a in ass: 
        print(a)

def pretty_print(bdd: _BDD, expr, true_only=False, keep_false_prefix=""):
    ass: list[dict[str, bool]] = get_assignments(bdd, expr)
    for a in ass:         
        if true_only:
            a = {k:v for k,v in a.items() if v or k[0] == keep_false_prefix}
        print(dict(sorted(a.items())))

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

    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand], ordering: list[ET], wavelengths = 2, other_order = True, generics_first = True, binary=True):
        self.bdd = _BDD()
        if has_cudd:
            print("Has cudd")
            self.bdd.configure(
                # number of bytes
                max_memory=50 * (2**30),
                reordering=False)
        else:
            self.bdd.configure(reordering=False)

        
        self.variables = []
        self.node_vars = {v:i for i,v in enumerate(topology.nodes)}
        self.edge_vars = {e:i for i,e in enumerate(topology.edges)} 
        self.demand_vars = demands
        self.binary_encoded_node_vars :list[str]= []
        self.binary_encoded_source_vars :list[str]= []
        self.binary_encoded_target_vars :list[str]= []
        self.wavelengths = wavelengths
        self.binary = binary
                
        self.encoding_counts = {
            BDD.ET.NODE: math.ceil(math.log2(len(self.node_vars))) if binary else len(self.node_vars),
            BDD.ET.EDGE:  math.ceil(math.log2(len(self.edge_vars))) if binary else len(self.edge_vars),
            BDD.ET.DEMAND:  math.ceil(math.log2(len(self.demand_vars)+1)) if binary else len(self.demand_vars),
            BDD.ET.PATH: len(self.edge_vars) * wavelengths * math.ceil(math.log2(len(self.demand_vars))) ,
            BDD.ET.SOURCE: math.ceil(math.log2(len(self.node_vars))) if binary else len(self.node_vars),
            BDD.ET.TARGET: math.ceil(math.log2(len(self.node_vars))) if binary else len(self.node_vars)
        }
        self.gen_vars(ordering, other_order, generics_first)
    
    # Demands, Paths, Lambdas, Edges, Nodes (T, N, S)
    def gen_vars(self, ordering: list[ET], other_order: bool = False, generic_first:bool = False):
        
        for type in ordering:
            if type == BDD.ET.DEMAND:
                    self.declare_variables(BDD.ET.DEMAND)
                    self.declare_variables(BDD.ET.DEMAND, 2)
            elif type == BDD.ET.PATH:
                    self.declare_path_variables(list(self.edge_vars.values()), self.wavelengths)
            elif type == BDD.ET.EDGE:
                self.declare_variables(BDD.ET.EDGE)
                self.declare_variables(BDD.ET.EDGE, 2)
            
            elif type in [BDD.ET.NODE,BDD.ET.SOURCE,BDD.ET.TARGET]:
                self.declare_variables(type)
            else: 
                raise Exception(f"Error: the given type {type} did not match any BDD type.")

    def declare_variables(self, type: ET, prefix_count: int = 1):
        d_bdd_vars = [f"{self.get_prefix_multiple(type, prefix_count)}{self.encoding_counts[type] - i}" for i in range(0,self.encoding_counts[type])]
        self.bdd.declare(*d_bdd_vars)
        
        return d_bdd_vars
        

    def declare_path_variables(self, es: list[int], ws: int):
        bdd_vars = []
        for e in es: 
            for d in range(self.encoding_counts[BDD.ET.DEMAND]):
                bdd_vars.append(f"{BDD.prefixes[BDD.ET.PATH]}_{e}_{d+1}^{BDD.prefixes[BDD.ET.LAMBDA]}")
                bdd_vars.append(f"{self.get_prefix_multiple(BDD.ET.PATH,2)}_{e}_{d+1}^{BDD.prefixes[BDD.ET.LAMBDA]}")


        for e in es: 

            for w in range(ws):
                for d in range(self.encoding_counts[BDD.ET.DEMAND]):
                    
                    bdd_vars.append(f"{BDD.prefixes[BDD.ET.PATH]}_{e}_{d+1}^{w}")
                    bdd_vars.append(f"{self.get_prefix_multiple(BDD.ET.PATH,2)}_{e}_{d+1}^{w}")
        
        self.bdd.declare(*bdd_vars)


    def make_subst_mapping(self, l1: list[str], l2: list[str]):
        return {l1_e: l2_e for (l1_e, l2_e) in zip(l1, l2)}
    

    def get_index(self, item, type: ET):
        if type == BDD.ET.NODE:
            return self.node_vars[item]

        if type == BDD.ET.EDGE:
            return self.edge_vars[item]

        if type == BDD.ET.DEMAND:
            assert isinstance(item, int)
            return item

        return 0
    
    def path_encode(self, edge: int, demand_num: int, l = None):
        encoding_count = self.encoding_counts[BDD.ET.DEMAND]
        encoding_expr = self.bdd.true
        for j in range(encoding_count):
            v = self.bdd.var(f"{BDD.prefixes[BDD.ET.PATH]}_{edge}_{j+1}^{BDD.prefixes[BDD.ET.LAMBDA] if l is None else l}")
            if not (demand_num >> (encoding_count - 1 - j)) & 1:
                v = ~v

            encoding_expr = encoding_expr & v
        return encoding_expr        

    
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

    def get_encoding_var_list(self, type: ET, override_prefix = None):
        vars = []
        if type == BDD.ET.PATH:     
            for e in self.edge_vars: 
                
                for d in range(self.encoding_counts[BDD.ET.DEMAND]):
    
                    vars.append(f"{BDD.prefixes[type] if override_prefix is None else override_prefix}_{self.get_index(e, BDD.ET.EDGE)}_{d+1}^{BDD.prefixes[BDD.ET.LAMBDA]}") 

            return vars

        return [f"{BDD.prefixes[type] if override_prefix is None else override_prefix}{i+1}" 
            for i in range(self.encoding_counts[type])]

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


class InBlock(Block):
    def __init__(self, topology: MultiDiGraph, base: BDD):
        self.expr = base.bdd.false
        
        in_edges = [(v, topology.in_edges(v, keys=True)) for v in topology.nodes]
        for (v, edges) in in_edges:
            for e in edges:
                v_enc = base.binary_encode(BDD.ET.NODE, base.get_index(v, BDD.ET.NODE))
                e_enc = base.binary_encode(BDD.ET.EDGE, base.get_index(e, BDD.ET.EDGE))

                self.expr = self.expr | (v_enc & e_enc)

class OutBlock(Block):
    def __init__(self, topology: MultiDiGraph, base: BDD):
        out_edges = [(v, topology.out_edges(v, keys=True)) for v in topology.nodes]
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

class SingleOutBlock(Block):
    def __init__(self, out_b: OutBlock, base:BDD):
        self.expr = base.bdd.true

        e_list = base.get_encoding_var_list(BDD.ET.EDGE)
        ee_list = base.get_encoding_var_list(BDD.ET.EDGE, base.get_prefix_multiple(BDD.ET.EDGE, 2))

        for d in base.demand_vars: 
            for e in base.edge_vars:
                for ee in base.edge_vars:
                    encoded_d = base.binary_encode(BDD.ET.DEMAND, d)
                    encoded_e = base.binary_encode(BDD.ET.EDGE, base.get_index(e, BDD.ET.EDGE))
                    encoded_ee = base.bdd.let(base.make_subst_mapping(e_list, ee_list), base.binary_encode(BDD.ET.EDGE, base.get_index(ee, BDD.ET.EDGE)))
                    out_e = out_b.expr
                    out_ee = base.bdd.let(base.make_subst_mapping(e_list, ee_list), out_b.expr)
                    p_var_e = base.path_encode(base.get_index(e, BDD.ET.EDGE), d)
                    p_var_ee = base.path_encode(base.get_index(ee, BDD.ET.EDGE), d)
                    equals = base.equals(e_list, ee_list)

                    u = encoded_d & encoded_e & encoded_ee & out_e & out_ee & p_var_e & p_var_ee
                    v = u.implies(equals)
                    self.expr = self.expr & v 
                
# class ChangedBlock(Block): 
#     def __init__(self, base: BDD):
#         self.expr = base.bdd.false


#         for e in base.edge_vars: 
#             encoded_e = base.binary_encode(BDD.ET.EDGE, e)
#             encoded_p = base.path_encode(e, d)
        



        # p_list = base.get_encoding_var_list(BDD.ET.PATH)
        # pp_list = base.get_encoding_var_list(BDD.ET.PATH, base.get_prefix_multiple(BDD.ET.PATH, 2))

        # passes2_subst = base.bdd.let(base.make_subst_mapping(p_list, pp_list), passes.expr)

        # self.expr = self.expr & passes.expr & ( ~passes2_subst)

        # Sørger for at kun 1 bit er flippet
        # only1Change = base.bdd.false
        # for p in range(len(p_list)):
        #     p_add = base.bdd.true
        #     for i in range(len(p_list)):
        #         pi_add = base.bdd.var(p_list[i]).equiv(base.bdd.var(pp_list[i]))
        #         if i == p: 
        #             pi_add = base.bdd.var(p_list[i]).equiv(base.bdd.true) & base.bdd.var(pp_list[i]).equiv(base.bdd.false)
        #         p_add = p_add & pi_add
        #     only1Change = only1Change | p_add
        
        # self.expr = self.expr & only1Change


class TrivialBlock(Block): 
    def __init__(self, target: TargetBlock, base: BDD):
        self.expr = base.bdd.false 
        s_list :list[str]= base.get_encoding_var_list(BDD.ET.NODE, base.prefixes[BDD.ET.SOURCE])
        v_list :list[str]= base.get_encoding_var_list(BDD.ET.NODE, base.prefixes[BDD.ET.NODE])

        for d in base.demand_vars: 
            d_expr = base.bdd.let(base.make_subst_mapping(v_list, s_list), target.expr)
            for e in base.edge_vars:
                d_expr = d_expr & ~base.path_encode(base.get_index(e, BDD.ET.EDGE),d)

            self.expr = self.expr | d_expr

        self.expr = self.expr
        

class PathBlock(Block): 
    def __init__(self, trivial : TrivialBlock, source: SourceBlock, target: TargetBlock, out : OutBlock, in_block : InBlock, singleOut: SingleOutBlock, base: BDD):
        path: Function = trivial.expr #path^0
        path_prev = None

        v_list = base.get_encoding_var_list(BDD.ET.NODE)
        e_list = base.get_encoding_var_list(BDD.ET.EDGE)
        s_list = base.get_encoding_var_list(BDD.ET.SOURCE)
        t_list = base.get_encoding_var_list(BDD.ET.TARGET)
        p_list = base.get_encoding_var_list(BDD.ET.PATH)
        pp_list = base.get_encoding_var_list(BDD.ET.PATH, base.get_prefix_multiple(BDD.ET.PATH, 2))

        out_subst = base.bdd.let(base.make_subst_mapping(v_list, s_list), out.expr)
        target_subst = base.bdd.let(base.make_subst_mapping(v_list, s_list), target.expr)

        singleOutSource = base.bdd.let(base.make_subst_mapping(v_list, s_list), singleOut.expr)

        all_exist_list :list[str]= v_list + e_list + pp_list


        while path != path_prev:   
            path_prev = path
            for d in base.demand_vars:
                encoded_d = base.binary_encode(BDD.ET.DEMAND,d)
                changed_expr = base.bdd.false

                for e in base.edge_vars:
                    d_expr = base.bdd.false

                    encoded_e = base.binary_encode(BDD.ET.EDGE,base.get_index(e, BDD.ET.EDGE))
                    encoded_p = base.path_encode(base.get_index(e, BDD.ET.EDGE),d)
                    encoded_pp = base.bdd.let(base.make_subst_mapping(p_list, pp_list), encoded_p)
                    # d_expr = d_expr & (encoded_p & ~encoded_pp)
                    for ee in base.edge_vars:
                        if e == ee: 
                            continue
                        v = base.path_encode(base.get_index(ee, BDD.ET.EDGE),d)  
                        vv = base.bdd.let(base.make_subst_mapping(p_list, pp_list), v)
                        d_expr = d_expr | ~((v & vv) | (~v & ~vv))
                    
                    d_expr = ~d_expr 
                    changed_expr = changed_expr | (encoded_e & encoded_p & ~encoded_pp & d_expr)

                subst = {}
                subst.update(base.make_subst_mapping(p_list, pp_list))
                subst.update(base.make_subst_mapping(s_list, v_list))
                prev_temp = base.bdd.let(subst, path_prev)
                        
                myExpr = out_subst & in_block.expr & ~source.expr & ~target_subst & changed_expr & prev_temp 
                res = myExpr.exist(*all_exist_list) & singleOutSource & encoded_d
                path = res | (trivial.expr) #path^k 

        self.expr = path 
        

class RoutingAndWavelengthBlock(Block):
    def __init__(self, base: BDD, source : SourceBlock, path :PathBlock):

        d_list = base.get_encoding_var_list(BDD.ET.DEMAND)
        s_list = base.get_encoding_var_list(BDD.ET.SOURCE)
        v_list = base.get_encoding_var_list(BDD.ET.NODE)
        e_list = base.get_encoding_var_list(BDD.ET.EDGE)
        ee_list = base.get_encoding_var_list(BDD.ET.EDGE, base.get_prefix_multiple(BDD.ET.EDGE, 2))

        vv = base.bdd.let(base.make_subst_mapping(v_list, s_list), source.expr)
        self.expr = vv

        for w in range(base.wavelengths): 
            encoded_p = base.get_encoding_var_list(BDD.ET.PATH)
            encoded_p_w = [p.replace(f"{BDD.prefixes[BDD.ET.LAMBDA]}", str(w)) for p in encoded_p]
            path_subst = base.bdd.let(base.make_subst_mapping(encoded_p, encoded_p_w), path.expr)

            self.expr = self.expr & path_subst

        self.expr = self.expr.exist(*(s_list + v_list + d_list + e_list + ee_list))

from timeit import default_timer as timer


class RWAProblem:
    def __init__(self, G: MultiDiGraph, demands: dict[int, Demand], ordering: list[BDD.ET], wavelengths: int, other_order = False, generics_first = False, with_sequence = False, wavelength_constrained=False, binary=True):
        s = timer()
        self.base = BDD(G, demands, ordering, wavelengths, other_order, generics_first, binary)

        in_expr = InBlock(G, self.base)
        out_expr = OutBlock(G, self.base)
        source = SourceBlock(self.base)
        target = TargetBlock( self.base)
        trivial_expr = TrivialBlock(target, self.base)
        singleOut = SingleOutBlock(out_expr, self.base)
        print("Building path BDD...")
        before_path = timer()
        path = PathBlock(trivial_expr, source, target, out_expr,in_expr, singleOut, self.base)
        after_path = timer()
        print(after_path - s,after_path - before_path, "Path built", flush=True)

        
        rwa = RoutingAndWavelengthBlock(self.base, source, path)
        self.rwa = rwa.expr
        e1 = timer()
        print(e1 - s, e1-s, "Blocks",  flush=True)


        # simplified = SimplifiedRoutingAndWavelengthBlock(rwa.expr & sequenceWavelengths.expr, self.base)
        
        #print(rwa.expr.count())
        # print((rwa.expr & sequenceWavelengths.expr).count())
        #print((sequenceWavelengths.expr).count())
        
        e2 = timer()
        print(e2 - s, e2-e1, "Sequence", flush=True)
        
        e3 = timer()
       # print(e3 - s, e3-e2, "Simplify",flush=True)

 
        e4 = timer()
        print(e4 - s, e4 - e3, "FullNoClash", flush=True)
        print("")
        
    def get_assignments(self, amount):
        assignments = []
        
        for a in self.base.bdd.pick_iter(self.rwa):
            
            if len(assignments) == amount:
                return assignments

            assignments.append(a)
        
        return assignments    
        
    
    def print_assignments(self, true_only=False, keep_false_prefix=""):
        pretty_print(self.base.bdd, self.rwa, true_only, keep_false_prefix=keep_false_prefix)
        
if __name__ == "__main__":
    pass
    # G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/simple_net.dot"))
    # if G.nodes.get("\\n") is not None:
    #     G.remove_node("\\n")

    # demands = {0: Demand("A", "B"),1: Demand("C", "B")}
    # RWAProblem(G, demands, 3)
    #print(base.bdd.vars)

    # print(get_assignments_block(base.bdd, trivial_expr))
    # source_expr = SourceBlock(base)
    # target_expr = TargetBlock(base)
    # singleIn_expr = SingleInBlock(in_expr, passes_expr, base)
    # singleOut_expr = SingleOutBlock(out_expr, passes_expr, base)
  

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