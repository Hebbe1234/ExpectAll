
from enum import Enum
try:
    from dd.cudd import BDD as _BDD
    from dd.cudd import Function
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
   DynamicBDD.dump(f"../out/{filename}", roots=[expr])

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

class DynamicBDD:

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

    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand], ordering: list[ET], wavelengths: int = 2, other_order:bool = False, generics_first:bool = False, init_demand=0, max_demands=32):
        self.bdd = _BDD()
        self.variables = []
        self.node_vars = {v:i for i,v in enumerate(topology.nodes)}
        self.edge_vars = {e:i for i,e in enumerate(topology.edges)} 
        self.demand_vars = {(init_demand+i):d for i,d in enumerate(demands.values())}
        self.encoded_node_vars :list[str]= []
        self.encoded_source_vars :list[str]= []
        self.encoded_target_vars :list[str]= []
        self.wavelengths = wavelengths
        self.init_demand=init_demand
                
        self.encoding_counts = {
            DynamicBDD.ET.NODE: math.ceil(math.log2(len(self.node_vars.keys()))),
            DynamicBDD.ET.EDGE:  math.ceil(math.log2(len(self.edge_vars.keys()))),
            DynamicBDD.ET.DEMAND:  math.ceil(math.log2(max_demands)),
            DynamicBDD.ET.PATH: len(self.edge_vars.keys()),
            DynamicBDD.ET.LAMBDA: max(1, math.ceil(math.log2(wavelengths))),
            DynamicBDD.ET.SOURCE: math.ceil(math.log2(len(self.node_vars.keys()))),
            DynamicBDD.ET.TARGET: math.ceil(math.log2(len(self.node_vars.keys()))),

        }
        self.bdd.configure(reordering=False)
        self.gen_vars(ordering, other_order, generics_first)

    
    # Demands, Paths, Lambdas, Edges, Nodes (T, N, S)
    def gen_vars(self, ordering: list[ET], other_order: bool = False, generic_first:bool = False):
        for type in ordering:
            if type == DynamicBDD.ET.DEMAND:
                    self.declare_variables(DynamicBDD.ET.DEMAND)
                    self.declare_variables(DynamicBDD.ET.DEMAND, 2)
            elif type == DynamicBDD.ET.PATH:
                    self.declare_generic_and_specific_variables(DynamicBDD.ET.PATH, list(self.edge_vars.values()), other_order, generic_first)
            elif type == DynamicBDD.ET.LAMBDA:
                self.declare_generic_and_specific_variables(DynamicBDD.ET.LAMBDA,  list(range(1, 1 + self.encoding_counts[DynamicBDD.ET.LAMBDA])), other_order, generic_first)
            elif type == DynamicBDD.ET.EDGE:
                self.declare_variables(DynamicBDD.ET.EDGE)
                self.declare_variables(DynamicBDD.ET.EDGE, 2)
            
            elif type in [DynamicBDD.ET.NODE,DynamicBDD.ET.SOURCE,DynamicBDD.ET.TARGET]:
                self.declare_variables(type)
            else: 
                raise Exception(f"Error: the given type {type} did not match any BDD type.")
                    
    def declare_variables(self, type: ET, prefix_count: int = 1):
        d_bdd_vars = [f"{self.get_prefix_multiple(type, prefix_count)}{self.encoding_counts[type] - i}" for i in range(0,self.encoding_counts[type])]
        self.bdd.declare(*d_bdd_vars)
        
        return d_bdd_vars
        

    def declare_generic_and_specific_variables(self, type: ET, l: list[int], other_order=False, generic_first=False):
        bdd_vars = []

        def append(item, demand):
            bdd_vars.append(f"{DynamicBDD.prefixes[type]}{item}_{demand}")
            bdd_vars.append(f"{self.get_prefix_multiple(type,2)}{item}_{demand}")
        
        def gen_generics():
            for item in l:
                bdd_vars.append(f"{DynamicBDD.prefixes[type]}{item}")
                bdd_vars.append(f"{self.get_prefix_multiple(type,2)}{item}")
        
        if generic_first:
            gen_generics()
        
        if other_order:
            for item in l:
                for demand in self.demand_vars.keys():
                    append(item, demand)
        else:
            for demand in self.demand_vars.keys():
                for item in l:
                    append(item, demand)
                
        if not generic_first:
            gen_generics()
        
        self.bdd.declare(*bdd_vars)


    def make_subst_mapping(self, l1: list[str], l2: list[str]):
        return {l1_e: l2_e for (l1_e, l2_e) in zip(l1, l2)}
    

    
    def get_p_var(self, edge: int, demand =  None, override = None):
        if override is None:
            return f"{DynamicBDD.prefixes[DynamicBDD.ET.PATH]}{edge}{f'_{demand}' if demand is not None else ''}"
        
        return f"{override}{edge}{f'_{demand}' if demand is not None else ''}"

    def get_p_vector(self, demand: int , override = None):
        l1 = []
        l2 = []
        for edge in  self.edge_vars.values():
            l1.append(self.get_p_var(edge, None, override))
            l2.append(self.get_p_var(edge, demand, override))

        return self.make_subst_mapping(l1, l2)
    
    def get_lam_var(self, wavelength: int, demand = None, override = None):
        if override is  None:
            return f"{DynamicBDD.prefixes[DynamicBDD.ET.LAMBDA]}{wavelength}{f'_{demand}' if demand is not None else ''}"
        
        return f"{override}{wavelength}{f'_{demand}' if demand is not None else ''}"
        



    def get_lam_vector(self, demand: int, override = None):
        l1 = []
        l2 = []
        for wavelength in  range(1,self.encoding_counts[DynamicBDD.ET.LAMBDA]+1):
            l1.append(self.get_lam_var(wavelength, None, override))
            l2.append(self.get_lam_var(wavelength, demand, override))

        return self.make_subst_mapping(l1, l2)


    def compile(self):
        return self.bdd

    def get_index(self, item, type: ET):
        if type == DynamicBDD.ET.NODE:
            return self.node_vars[item]

        if type == DynamicBDD.ET.EDGE:
            return self.edge_vars[item]

        if type == DynamicBDD.ET.DEMAND:
            assert isinstance(item, int)
            return item

        return 0
    
    

    def binary_encode(self, type: ET, number: int):
        encoding_count = self.encoding_counts[type]
        encoding_expr = self.bdd.true
        for j in range(encoding_count):
            v = self.bdd.var(f"{DynamicBDD.prefixes[type]}{j+1}")
            if not (number >> (encoding_count - 1 - j)) & 1:
                v = ~v

            encoding_expr = encoding_expr & v
          
        return encoding_expr
    
    def binary_encode_as_list_of_variables(self, type: ET, number: int):
        encoding_count = self.encoding_counts[type]

        variables :list[Function]= []        
        for j in range(encoding_count):
            v = self.bdd.var(f"{DynamicBDD.prefixes[type]}{j+1}")
            if not (number >> (encoding_count - 1 - j)) & 1:
                v = ~v
            variables.append(v)
        
        return variables


    def get_prefix_multiple(self, type: ET, multiple: int):
        return "".join([DynamicBDD.prefixes[type] for _ in range(multiple)])

    def get_encoding_var_list(self, type: ET, override_prefix = None):
        offset = 0
        if type == DynamicBDD.ET.PATH:
            offset = 1

        return [f"{DynamicBDD.prefixes[type] if override_prefix is None else override_prefix}{i+1 - offset}" for i in range(self.encoding_counts[type])]

    def equals(self, e1: list[str], e2: list[str]):
        assert len(e1) == len(e2)

        expr = self.bdd.true
        for (var1, var2) in zip(e1,e2):
            s = (self.bdd.var(var1) & self.bdd.var(var2)) |(~self.bdd.var(var1) & ~self.bdd.var(var2))
            expr = expr & s

        return expr




class Block:
    def __init__(self, base: DynamicBDD):
        self.expr = base.bdd.true


class InBlock(Block):
    def __init__(self, topology: MultiDiGraph, base: DynamicBDD):
        self.expr = base.bdd.false
        
        in_edges = [(v, topology.in_edges(v, keys=True)) for v in topology.nodes]
        for (v, edges) in in_edges:
            for e in edges:
                v_enc = base.binary_encode(DynamicBDD.ET.NODE, base.get_index(v, DynamicBDD.ET.NODE))
                e_enc = base.binary_encode(DynamicBDD.ET.EDGE, base.get_index(e, DynamicBDD.ET.EDGE))

                self.expr = self.expr | (v_enc & e_enc)

class OutBlock(Block):
    def __init__(self, topology: MultiDiGraph, base: DynamicBDD):
        out_edges = [(v, topology.out_edges(v, keys=True)) for v in topology.nodes]
        self.expr = base.bdd.false

        for (v, edges) in out_edges:
            for e in edges:
                v_enc = base.binary_encode(DynamicBDD.ET.NODE, base.get_index(v, DynamicBDD.ET.NODE))
                e_enc = base.binary_encode(DynamicBDD.ET.EDGE, base.get_index(e, DynamicBDD.ET.EDGE))

                self.expr = self.expr | (v_enc & e_enc)

class SourceBlock(Block):
    def __init__(self, base: DynamicBDD):
        self.expr = base.bdd.false

        for i, demand in base.demand_vars.items():
            v_enc = base.binary_encode(DynamicBDD.ET.NODE, base.get_index(demand.source, DynamicBDD.ET.NODE))
            d_enc = base.binary_encode(DynamicBDD.ET.DEMAND, base.get_index(i, DynamicBDD.ET.DEMAND))
            self.expr = self.expr | (v_enc & d_enc)

class TargetBlock(Block):
    def __init__(self, base: DynamicBDD):
        self.expr = base.bdd.false

        for i, demand in base.demand_vars.items():
            v_enc = base.binary_encode(DynamicBDD.ET.NODE, base.get_index(demand.target, DynamicBDD.ET.NODE))
            d_enc = base.binary_encode(DynamicBDD.ET.DEMAND, base.get_index(i, DynamicBDD.ET.DEMAND))
            self.expr = self.expr | (v_enc & d_enc)

class PassesBlock(Block):
    def __init__(self, topology: MultiDiGraph, base: DynamicBDD):
        self.expr = base.bdd.false
        for edge in topology.edges:
            e_enc = base.binary_encode(DynamicBDD.ET.EDGE, base.get_index(edge, DynamicBDD.ET.EDGE))
            p_var = base.bdd.var(base.get_p_var(base.get_index(edge, DynamicBDD.ET.EDGE)))
            self.expr = self.expr | (e_enc & p_var)

class SingleInBlock(Block):
    def __init__(self, in_b: InBlock, passes: PassesBlock, base:DynamicBDD):
        self.expr = base.bdd.true

        e_list = base.get_encoding_var_list(DynamicBDD.ET.EDGE)
        ee_list = base.get_encoding_var_list(DynamicBDD.ET.EDGE, base.get_prefix_multiple(DynamicBDD.ET.EDGE, 2))

        in_1 = in_b.expr
        in_2 = base.bdd.let(base.make_subst_mapping(e_list, ee_list), in_b.expr)

        passes_1 = passes.expr
        passes_2 = base.bdd.let(base.make_subst_mapping(e_list, ee_list), passes.expr)

        equals = base.equals(e_list, ee_list)
        u = in_1 & in_2 & passes_1 & passes_2
        v = u.implies(equals)

        self.expr = base.bdd.forall(e_list + ee_list, v)
        
class SingleOutBlock(Block):
    def __init__(self, out_b: OutBlock, passes: PassesBlock, base:DynamicBDD):
        self.expr = base.bdd.true

        e_list = base.get_encoding_var_list(DynamicBDD.ET.EDGE)
        ee_list = base.get_encoding_var_list(DynamicBDD.ET.EDGE, base.get_prefix_multiple(DynamicBDD.ET.EDGE, 2))

        out_1 = out_b.expr
        out_2 = base.bdd.let(base.make_subst_mapping(e_list, ee_list), out_b.expr)

        passes_1 = passes.expr
        passes_2 = base.bdd.let(base.make_subst_mapping(e_list, ee_list), passes.expr)

        equals = base.equals(e_list, ee_list)
        u = out_1 & out_2 & passes_1 & passes_2
        v = u.implies(equals)

        self.expr = base.bdd.forall(e_list + ee_list, v)        

class SingleWavelengthBlock(Block):
    def __init__(self, base: DynamicBDD):
        self.expr = base.bdd.false
        for i in range(base.wavelengths):
            self.expr = self.expr | base.binary_encode(DynamicBDD.ET.LAMBDA, i)

class NoClashBlock(Block):
    def __init__(self, passes: PassesBlock, base: DynamicBDD):
        self.expr = base.bdd.false

        passes_1 = passes.expr
        mappingP = {f"{DynamicBDD.prefixes[DynamicBDD.ET.PATH]}{i}": f"{base.get_prefix_multiple(DynamicBDD.ET.PATH,2)}{i}" for i in range(base.encoding_counts[DynamicBDD.ET.PATH])}
        passes_2: Function = passes.expr.let(**mappingP)
        
        l_list = base.get_encoding_var_list(DynamicBDD.ET.LAMBDA)
        ll_list =base.get_encoding_var_list(DynamicBDD.ET.LAMBDA, base.get_prefix_multiple(DynamicBDD.ET.LAMBDA, 2))
        
        d_list = base.get_encoding_var_list(DynamicBDD.ET.DEMAND)
        dd_list = base.get_encoding_var_list(DynamicBDD.ET.DEMAND, base.get_prefix_multiple(DynamicBDD.ET.DEMAND, 2))
        
        e_list = base.get_encoding_var_list(DynamicBDD.ET.EDGE)
        
        u = (passes_1 & passes_2).exist(*e_list)
        self.expr = u.implies(~base.equals(l_list, ll_list) | base.equals(d_list, dd_list))
        
class ChangedBlock(Block): 
    def __init__(self, passes: PassesBlock,  base: DynamicBDD):
        self.expr = base.bdd.true
        p_list = base.get_encoding_var_list(DynamicBDD.ET.PATH)
        pp_list = base.get_encoding_var_list(DynamicBDD.ET.PATH, base.get_prefix_multiple(DynamicBDD.ET.PATH, 2))

        passes2_subst = base.bdd.let(base.make_subst_mapping(p_list, pp_list), passes.expr)

        self.expr = self.expr & passes.expr & ( ~passes2_subst)

        # Sørger for at kun 1 bit er flippet
        only1Change = base.bdd.false
        for p in range(len(p_list)):
            p_add = base.bdd.true
            for i in range(len(p_list)):
                pi_add = base.bdd.var(p_list[i]).equiv(base.bdd.var(pp_list[i]))
                if i == p: 
                    pi_add = base.bdd.var(p_list[i]).equiv(base.bdd.true) & base.bdd.var(pp_list[i]).equiv(base.bdd.false)
                p_add = p_add & pi_add
            only1Change = only1Change | p_add
        
        self.expr = self.expr & only1Change


class TrivialBlock(Block): 
    def __init__(self, topology: MultiDiGraph,  base: DynamicBDD):
        self.expr = base.bdd.true 
        s_encoded :list[str]= base.get_encoding_var_list(DynamicBDD.ET.NODE, base.prefixes[DynamicBDD.ET.SOURCE])
        t_encoded :list[str]= base.get_encoding_var_list(DynamicBDD.ET.NODE, base.prefixes[DynamicBDD.ET.TARGET])

        self.expr = self.expr & base.equals(s_encoded, t_encoded)

        for e in topology.edges: 
            p_var :str = base.get_p_var(base.get_index(e, DynamicBDD.ET.EDGE)) 
            self.expr = self.expr & (~base.bdd.var(p_var))

class PathBlock(Block): 
    def __init__(self, topology: digraph.DiGraph, trivial : TrivialBlock, out : OutBlock, in_block : InBlock, changed: ChangedBlock, singleIn: SingleInBlock, singleOut: SingleOutBlock, base: DynamicBDD):
        path : Function = base.bdd.false #path^0
        path_prev = None

        v_list = base.get_encoding_var_list(DynamicBDD.ET.NODE)
        e_list = base.get_encoding_var_list(DynamicBDD.ET.EDGE)
        s_list = base.get_encoding_var_list(DynamicBDD.ET.SOURCE)
        pp_list = base.get_encoding_var_list(DynamicBDD.ET.PATH, base.get_prefix_multiple(DynamicBDD.ET.PATH, 2))
        p_list = base.get_encoding_var_list(DynamicBDD.ET.PATH)

        forAllSingleInOut = (singleIn.expr & singleOut.expr).forall(*v_list)
        all_exist_list :list[str]= v_list + e_list + pp_list

        out_subst = base.bdd.let(base.make_subst_mapping(v_list, s_list), out.expr)

        while path != path_prev:
            path_prev = path
            subst = {}
            subst.update(base.make_subst_mapping(p_list, pp_list))
            subst.update(base.make_subst_mapping(s_list, v_list))
            prev_temp = base.bdd.let(subst, path_prev)
                    
            myExpr = out_subst & in_block.expr & changed.expr & prev_temp 
            res = myExpr.exist(*all_exist_list) & forAllSingleInOut
            path = res | (trivial.expr)

        self.expr = path 
        

class DemandPathBlock(Block):
    def __init__(self, path : PathBlock, source : SourceBlock, target : TargetBlock, singleIn: SingleInBlock, singleOut: SingleOutBlock,  base: DynamicBDD):

        v_list = base.get_encoding_var_list(DynamicBDD.ET.NODE)
        s_list = base.get_encoding_var_list(DynamicBDD.ET.SOURCE)
        t_list = base.get_encoding_var_list(DynamicBDD.ET.TARGET)

        source_subst = base.bdd.let(base.make_subst_mapping(v_list, s_list), source.expr)
        target_subst = base.bdd.let(base.make_subst_mapping(v_list, t_list), target.expr)


        self.expr = (path.expr & source_subst & target_subst).exist(*s_list + t_list)
        

class RoutingAndWavelengthBlock(Block):
    def __init__(self, demandPath : DemandPathBlock, wavelength: SingleWavelengthBlock, base: DynamicBDD, constrained=False):

        d_list = base.get_encoding_var_list(DynamicBDD.ET.DEMAND)
        l_list = base.get_encoding_var_list(DynamicBDD.ET.LAMBDA)
        self.expr = base.bdd.true

        for i in base.demand_vars.keys():
            
            wavelength_subst = base.bdd.false
            
            if constrained:
                for w in range(min(base.wavelengths, i+1)):
                    wavelength_subst |= base.bdd.let(base.get_lam_vector(i),base.binary_encode(DynamicBDD.ET.LAMBDA, w))
            else:
                wavelength_subst = base.bdd.let(base.get_lam_vector(i),wavelength.expr)

        
            demandPath_subst = base.bdd.let(base.get_p_vector(i),demandPath.expr)
            self.expr = (self.expr &  (demandPath_subst & wavelength_subst & base.binary_encode(base.ET.DEMAND, i)).exist(*(d_list+l_list)))

class SimplifiedRoutingAndWavelengthBlock(Block):
    def __init__(self, rwb: Function, base: DynamicBDD):
        ps = sum([list(base.get_p_vector(d).values()) for d in base.demand_vars.keys()],[])
        all_lambdas = rwb.exist(*ps)
        # remaining_lambdas = list(base.bdd.pick_iter(all_lambdas))
        
        remaining = all_lambdas

        
        assignment = base.bdd.pick(remaining)
        i = 0
        while assignment is not None and i < 100000:
            print(remaining.count())
            lambdas = self.identify_lambdas(assignment, base)
            transformations = self.transform(lambdas, base)
            remove_expr = base.bdd.false
            for t in transformations:
                newLambdas = {d: t[l] for d,l in lambdas.items()}
                d_expr = base.bdd.true
                for d,l in newLambdas.items():
                    d_expr &= base.bdd.let(base.get_lam_vector(int(d)),base.binary_encode(DynamicBDD.ET.LAMBDA, l))
                
                remove_expr |= d_expr
            i += 1
            
            # expr = self.assignment_to_expr(assignment, base)
            
            remaining = remaining & ~(remove_expr)
            assignment = base.bdd.pick(remaining) 
            
        # while len(remaining_lambdas) != 0:
        #     pass
    def assignment_to_expr(self, assignment: dict[str, bool], base: DynamicBDD):
        expr = base.bdd.true
        for k,v in assignment.items():
            expr &= base.bdd.var(k) if v else ~base.bdd.var(k)
        
        return expr
    
    def identify_lambdas(self, assignment: dict[str, bool], base: DynamicBDD):
        def power(l_var: str):
            val = int(l_var.replace(base.prefixes[DynamicBDD.ET.LAMBDA], ""))
            return 2 ** (base.encoding_counts[DynamicBDD.ET.LAMBDA] - val)
        
        colors = {str(k):0 for k in base.demand_vars.keys()}

        for k, v in assignment.items():     
            if k[0] == base.prefixes[DynamicBDD.ET.LAMBDA] and v:
                [l_var, demand_id] = k.split("_")
                colors[demand_id] += power(l_var)

        return colors 
        
    def transform(self, assignment: dict[str, int], base: DynamicBDD):
        lambdas = set(list(assignment.values()))
        transformations = []
        perms = permutations(range(base.wavelengths), len(lambdas))
        print(len(list(perms)), len(lambdas))
        for p in  permutations(range(base.wavelengths), len(lambdas)):
            transformations.append({k:p[i] for i, k in enumerate(lambdas)})

        return transformations

from timeit import default_timer as timer


class SequenceWavelengthsBlock(Block):
    def __init__(self, rwb: RoutingAndWavelengthBlock, base: DynamicBDD):
        self.expr = base.bdd.false
        e0 = timer()
        
        test_d = {}
        for d in base.demand_vars:
            test_d[d] = base.get_lam_vector(int(d))
        

        test_l = {}
        for l in range(base.wavelengths):
            test_l[l] = base.binary_encode(DynamicBDD.ET.LAMBDA, l)
        
        u_times = []
        i_times = []
        for l in range(base.wavelengths):
            p = base.bdd.false
            for d in base.demand_vars:
                p |= base.bdd.let(test_d[d],test_l[l])

            u = base.bdd.false
            e0 = timer()
            
            if l == 0:
                u = base.bdd.false
            
            for l_prime in range(l-1,l):
                if l_prime == -1:
                    break
                
                ld_prime = base.bdd.false
                for d in base.demand_vars:
                    ld_prime |= base.bdd.let(test_d[d],test_l[l_prime])
                    
                ld_prime = ~ld_prime
                u |=ld_prime
            
            e1 = timer()
            u_times.append(e1-e0)
            
            
            self.expr |= ~(~p | ~u)
            
            e2 = timer()
            i_times.append(e2-e1)
        
        self.expr = ~self.expr
                
class FullNoClashBlock(Block):
    def __init__(self,  rwa: Function, noClash : NoClashBlock, base: DynamicBDD):
        self.expr = rwa
        d_list = base.get_encoding_var_list(DynamicBDD.ET.DEMAND)
        dd_list = base.get_encoding_var_list(DynamicBDD.ET.DEMAND, base.get_prefix_multiple(DynamicBDD.ET.DEMAND, 2))
        pp_list = base.get_encoding_var_list(DynamicBDD.ET.PATH, base.get_prefix_multiple(DynamicBDD.ET.PATH, 2))
        ll_list = base.get_encoding_var_list(DynamicBDD.ET.LAMBDA, base.get_prefix_multiple(DynamicBDD.ET.LAMBDA, 2))
        
        d_expr = []

        for i in base.demand_vars.keys():
            noClash_subst = base.bdd.true

            for j in base.demand_vars.keys():
                if i < j:
                    continue
                
                subst = {}
                subst.update(base.get_p_vector(i))
                subst.update(base.make_subst_mapping(pp_list, list(base.get_p_vector(j).values())))

                subst.update(base.get_lam_vector(i))
                subst.update(base.make_subst_mapping(ll_list, list(base.get_lam_vector(j).values())))
                noClash_subst = base.bdd.let(subst, noClash.expr) & base.binary_encode(base.ET.DEMAND, i) & base.bdd.let(base.make_subst_mapping(d_list, dd_list), base.binary_encode(base.ET.DEMAND, j)) 
                d_expr.append(noClash_subst.exist(*(d_list + dd_list)))
        
        i_l = 0
        for i in range(0, len(d_expr),3):
            i_l = i
            if i > len(d_expr) - 3:
                break
            
            
            # print(f"{i}/{len(d_expr)}")
            d_e1 = d_expr[i]
            d_e2 = d_expr[i+1]
            d_e3 = d_expr[i+2]
            d_e = d_e1 & d_e2 & d_e3 
            self.expr = self.expr & d_e   

        
        for j in range(i_l, len(d_expr)):
            
            # print(f"{j}/{len(d_expr)}")
            d_e = d_expr[j] 
            self.expr = self.expr & d_e

            
             

class DynamicRWAProblem:
    def __init__(self, G: MultiDiGraph, demands: dict[int, Demand], ordering: list[DynamicBDD.ET], wavelengths: int, other_order = False, generics_first = False, with_sequence = False, wavelength_constrained=False, init_demand=0):
        s = timer()
        self.base = DynamicBDD(G, demands, ordering, wavelengths, other_order, generics_first, init_demand)
        in_expr = InBlock(G, self.base)
        out_expr = OutBlock(G, self.base)
        source = SourceBlock(self.base)
        target = TargetBlock( self.base)
        trivial_expr = TrivialBlock(G, self.base)
        passes_expr = PassesBlock(G, self.base)
        singleIn = SingleInBlock(in_expr, passes_expr, self.base)
        singleOut = SingleOutBlock(out_expr, passes_expr, self.base)
        passes = PassesBlock(G, self.base)
        changed = ChangedBlock(passes, self.base)
        print("Building pathDynamicBDD...")
        before_path = timer()
        path = PathBlock(G, trivial_expr, out_expr,in_expr, changed, singleIn, singleOut, self.base)
        after_path = timer()
        print("Total: ",after_path - s, "Path built: ",after_path - before_path)
        demandPath = DemandPathBlock(path,source,target,singleIn, singleOut,self.base)
        singleWavelength_expr = SingleWavelengthBlock(self.base)
        noClash_expr = NoClashBlock(passes_expr, self.base) 
        
        rwa = RoutingAndWavelengthBlock(demandPath, singleWavelength_expr, self.base, constrained=wavelength_constrained)
        
        e1 = timer()
        print(e1 - s, e1-s, "Blocks",  flush=True)

        sequenceWavelengths = self.base.bdd.true
        if with_sequence:
            sequenceWavelengths = SequenceWavelengthsBlock(rwa, self.base)
        
        # simplified = SimplifiedRoutingAndWavelengthBlock(rwa.expr & sequenceWavelengths.expr, self.base)
        
        #print(rwa.expr.count())
        # print((rwa.expr & sequenceWavelengths.expr).count())
        #print((sequenceWavelengths.expr).count())
        
        e2 = timer()
        print(e2 - s, e2-e1, "Sequence", flush=True)
        full = rwa.expr #& sequenceWavelengths.expr
        
        if with_sequence:
            full = full & sequenceWavelengths.expr
            
        e3 = timer()
       # print(e3 - s, e3-e2, "Simplify",flush=True)

        fullNoClash = FullNoClashBlock(rwa.expr, noClash_expr, self.base)
        self.rwa = fullNoClash.expr
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
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/four_node.dot"))

    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
        
    demands = {0: Demand("A", "B"), 
               1: Demand("B", "D"), 
               }
    
    types = [DynamicBDD.ET.LAMBDA,DynamicBDD.ET.DEMAND,DynamicBDD.ET.PATH,DynamicBDD.ET.EDGE,DynamicBDD.ET.SOURCE,DynamicBDD.ET.TARGET,DynamicBDD.ET.NODE]

    rw1 = DynamicRWAProblem(G, demands, types, 5, other_order =True, generics_first=False, init_demand=5)
    print(rw1.rwa.count())
    print(rw1.base.bdd.vars)
  
