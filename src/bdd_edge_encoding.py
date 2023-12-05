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
    print("prettyprint: ")
    ass: list[dict[str, bool]] = get_assignments(bdd, expr)
    for a in ass:         
        if true_only:
            a = {k:v for k,v in a.items() if v or k[0] == keep_false_prefix}
        print(dict(sorted(a.items())), flush=True)

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
        ET.LAMBDA: "L",
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

        #print("nodevars", self.node_vars)
        #print("edgevars", self.edge_vars)
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
          #  print(e, [i for i in self.edge_vars if self.edge_vars[i] == e])
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
                    encoded_ee = base.bdd.let(base.make_subst_mapping(e_list, ee_list),
                                              base.binary_encode(BDD.ET.EDGE, base.get_index(ee, BDD.ET.EDGE)))
                    out_e = out_b.expr
                    out_ee = base.bdd.let(base.make_subst_mapping(e_list, ee_list), out_b.expr)
                    p_var_e = base.path_encode(base.get_index(e, BDD.ET.EDGE), d)
                    p_var_ee = base.path_encode(base.get_index(ee, BDD.ET.EDGE), d)
                    
                    equals = base.equals(e_list, ee_list)

                    u = encoded_d & encoded_e & encoded_ee & out_e & out_ee & p_var_e & p_var_ee
                    
                    v = u.implies(equals)
                
                    self.expr = self.expr & v.exist(*e_list)
        

class TrivialBlock(Block): 
    def __init__(self, target: TargetBlock, base: BDD):
        self.expr = base.bdd.false 
        s_list :list[str]= base.get_encoding_var_list(BDD.ET.NODE, base.prefixes[BDD.ET.SOURCE])
        v_list :list[str]= base.get_encoding_var_list(BDD.ET.NODE, base.prefixes[BDD.ET.NODE])

        for d in base.demand_vars: 
            d_expr = base.binary_encode(BDD.ET.DEMAND, d) & base.bdd.let(base.make_subst_mapping(v_list, s_list), target.expr) 
            for e in base.edge_vars:
                d_expr = d_expr & ~base.path_encode(base.get_index(e, BDD.ET.EDGE),d)

            self.expr = self.expr | d_expr


class PathBlock(Block): 
    def __init__(self, trivial : TrivialBlock, source: SourceBlock, target: TargetBlock,
                  out : OutBlock, in_block : InBlock, singleOut: SingleOutBlock, base: BDD):
        
        self.expr = base.bdd.false
       
        v_list = base.get_encoding_var_list(BDD.ET.NODE)
        e_list = base.get_encoding_var_list(BDD.ET.EDGE)
        s_list = base.get_encoding_var_list(BDD.ET.SOURCE)
        t_list = base.get_encoding_var_list(BDD.ET.TARGET)
        d_list = base.get_encoding_var_list(BDD.ET.DEMAND)
        p_list = base.get_encoding_var_list(BDD.ET.PATH)
        pp_list = base.get_encoding_var_list(BDD.ET.PATH, base.get_prefix_multiple(BDD.ET.PATH, 2))

        out_subst = base.bdd.let(base.make_subst_mapping(v_list, s_list), out.expr)
        source_subst = base.bdd.let(base.make_subst_mapping(v_list, s_list), source.expr)
        target_subst = base.bdd.let(base.make_subst_mapping(v_list, s_list), target.expr)

        singleOutSource = base.bdd.let(base.make_subst_mapping(v_list, s_list), singleOut.expr)
        
        all_exist_list :list[str]= v_list + e_list + pp_list

        for d in base.demand_vars:
            
            encoded_d = base.binary_encode(BDD.ET.DEMAND,d)
            path: Function = trivial.expr #path^0
            path_prev = None

            while path != path_prev:   
                path_prev = path
                changed_expr = base.bdd.false

                for e in base.edge_vars:
                    d_expr = base.bdd.true

                    encoded_e = base.binary_encode(BDD.ET.EDGE,base.get_index(e, BDD.ET.EDGE))
                    encoded_p = base.path_encode(base.get_index(e, BDD.ET.EDGE),d)
                    encoded_pp = base.bdd.let(base.make_subst_mapping(p_list, pp_list), encoded_p)
                    # d_expr = d_expr & (encoded_p & ~encoded_pp)
                    for ee in base.edge_vars:
                        if e == ee: 
                            continue
                        v = base.path_encode(base.get_index(ee, BDD.ET.EDGE),d)  
                        vv = base.bdd.let(base.make_subst_mapping(p_list, pp_list), v)
                        d_expr = d_expr & ((v & vv) | (~v & ~vv))
                                        
                    changed_expr = changed_expr | (encoded_e & encoded_p & ~encoded_pp & d_expr)

                subst = {}
                subst.update(base.make_subst_mapping(p_list, pp_list))
                subst.update(base.make_subst_mapping(s_list, v_list))
                prev_temp = base.bdd.let(subst, path_prev)
                        
                        
                myExpr = out_subst & in_block.expr & ~source.expr & ~target_subst & changed_expr & prev_temp  & singleOutSource
                res = myExpr.exist(*all_exist_list) 
                
                path =  encoded_d & ((res) | (source_subst & path))

            self.expr = self.expr | path
            
        

class SingleWavelengthBlock(Block): 
    def __init__(self, source: SourceBlock, out : OutBlock, base: BDD):
        
        d_list = base.get_encoding_var_list(BDD.ET.DEMAND)
        v_list = base.get_encoding_var_list(BDD.ET.NODE)
        s_list = base.get_encoding_var_list(BDD.ET.SOURCE)
        e_list = base.get_encoding_var_list(BDD.ET.EDGE)
        ee_list = base.get_encoding_var_list(BDD.ET.EDGE, base.get_prefix_multiple(BDD.ET.EDGE, 2))

        source_subst = base.bdd.let(base.make_subst_mapping(v_list, s_list), source.expr)
        out_subst = base.bdd.let(base.make_subst_mapping(v_list, s_list), out.expr)

        self.expr = base.bdd.true

        for d in base.demand_vars : 
            encoded_d = base.binary_encode(BDD.ET.DEMAND,d)
            my_expr_outer = (encoded_d & source_subst)
            my_expr_mid = base.bdd.true
            for w in range(base.wavelengths):
                for e in reversed(base.edge_vars): 
                    encoded_demand_on_edge = base.path_encode(base.get_index(e, BDD.ET.EDGE), d, w)

                    encoded_e = base.binary_encode(BDD.ET.EDGE, base.get_index(e, BDD.ET.EDGE))

                    left_impl = (encoded_e & out_subst & encoded_demand_on_edge).exist(*(e_list))
                    right_impl = base.bdd.true
                    for ee in base.edge_vars : 
                        for ww in range(base.wavelengths): 
                            if w == ww: 
                                continue

                            encoded_ee = base.bdd.let(base.make_subst_mapping(e_list, ee_list),
                                                        base.binary_encode(BDD.ET.EDGE, base.get_index(ee, BDD.ET.EDGE)))
                            out_ee = base.bdd.let(base.make_subst_mapping(e_list, ee_list), out_subst)

                            encoded_demand_on_edge_2 = base.path_encode(base.get_index(ee, BDD.ET.EDGE), d, ww)
                        
                            right_impl = right_impl &  (encoded_ee & out_ee & ~encoded_demand_on_edge_2).exist(*ee_list)

                    my_expr_mid = (my_expr_mid & (left_impl.implies(right_impl)))

            self.expr = self.expr & (my_expr_outer & my_expr_mid).exist(*(d_list + s_list))


class NoExtraDemands(Block):
    def __init__(self, base: BDD):

        e_list = base.get_encoding_var_list(BDD.ET.EDGE)

        self.expr = base.bdd.true

        for e in base.edge_vars: 
            encoded_e = base.binary_encode(BDD.ET.EDGE, base.get_index(e, BDD.ET.EDGE))
            d_expr = base.bdd.false

            for d in base.demand_vars:
                encoded_demand_on_edge = base.path_encode(base.get_index(e, BDD.ET.EDGE), d)
                d_expr = d_expr | encoded_demand_on_edge

            encoded_demand_on_edge_0 = base.path_encode(base.get_index(e, BDD.ET.EDGE), 0)
            implication = (~(d_expr)).implies(encoded_demand_on_edge_0)

            self.expr = self.expr & (encoded_e & implication).exist(*(e_list))



class RoutingAndWavelengthBlock(Block):
    def __init__(self, base: BDD, source : SourceBlock, path :PathBlock,  no_extra_demands : NoExtraDemands):

        d_list = base.get_encoding_var_list(BDD.ET.DEMAND)
        s_list = base.get_encoding_var_list(BDD.ET.SOURCE)
        v_list = base.get_encoding_var_list(BDD.ET.NODE)
        e_list = base.get_encoding_var_list(BDD.ET.EDGE)

        source_subst = base.bdd.let(base.make_subst_mapping(v_list, s_list), source.expr)

        self.expr = base.bdd.true

        for d in base.demand_vars: 
            d_encoded = base.binary_encode(BDD.ET.DEMAND, d)
            d_s_exist = source_subst & d_encoded
            
            path_expr = base.bdd.false
            no_weird_demand = base.bdd.true

            for w in range(base.wavelengths):
                encoded_p_list = base.get_encoding_var_list(BDD.ET.PATH)
                encoded_p_w_list = [p.replace(f"{BDD.prefixes[BDD.ET.LAMBDA]}", str(w)) for p in encoded_p_list]

                path_subst = base.bdd.let(base.make_subst_mapping(encoded_p_list, encoded_p_w_list), path.expr)
                no_rouge_p_vars = base.bdd.true
                for ww in range(base.wavelengths): 
                    if w == ww: 
                        continue
                    lambda_expr = base.bdd.true

                    for e in base.edge_vars: 
                        ee = base.get_index(e, BDD.ET.EDGE)
                        encoded_e = base.binary_encode(BDD.ET.EDGE, ee)
                        p_var = base.path_encode(ee, d, ww)
                        lambda_expr = lambda_expr & (encoded_e & ~p_var).exist(*e_list)

                    no_rouge_p_vars = no_rouge_p_vars & lambda_expr
                    
                path_expr = path_expr | (path_subst & no_rouge_p_vars)
                encoded_p_list = base.get_encoding_var_list(BDD.ET.PATH)
                encoded_p_w_list = [p.replace(f"{BDD.prefixes[BDD.ET.LAMBDA]}", str(w)) for p in encoded_p_list]

                no_weird_demand_subst = base.bdd.let(base.make_subst_mapping(encoded_p_list, encoded_p_w_list), no_extra_demands.expr)
                no_weird_demand = no_weird_demand & no_weird_demand_subst
            

            self.expr = self.expr & (d_s_exist & path_expr & no_weird_demand).exist(*(d_list + s_list))

            

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

        only = NoExtraDemands(self.base)
        
        rwa = RoutingAndWavelengthBlock(self.base, source, path, only) 
        self.rwa = rwa.expr

        e1 = timer()
        print(e1 - s, e1-s, "Blocks",  flush=True)

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