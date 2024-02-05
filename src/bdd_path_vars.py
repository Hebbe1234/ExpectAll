from enum import Enum
import time

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

    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand], ordering: list[ET], paths, overlapping_paths, wavelengths = 2, group_by_edge_order = True, interleave_lambda_binary_vars=True, generics_first = True, binary=True, reordering=False):
        self.bdd = _BDD()
        if has_cudd:
            print("Has cudd")
            self.bdd.configure(
                # number of bytes
                max_memory=50 * (2**30),
                reordering=reordering)
        else:
            self.bdd.configure(reordering=reordering)

        
        self.variables = []
        self.node_vars = {v:i for i,v in enumerate(topology.nodes)}
        self.edge_vars = {e:i for i,e in enumerate(topology.edges(keys=True))} 
        self.demand_vars = demands
        self.encoded_node_vars :list[str]= []
        self.encoded_source_vars :list[str]= []
        self.encoded_target_vars :list[str]= []
        self.wavelengths = wavelengths
        self.paths = paths
        self.overlapping_paths = overlapping_paths
        self.binary = binary
                
        self.encoding_counts = {
            BDD.ET.NODE: math.ceil(math.log2(len(self.node_vars))) if binary else len(self.node_vars),
            BDD.ET.EDGE:  math.ceil(math.log2(len(self.edge_vars))) if binary else len(self.edge_vars),
            BDD.ET.DEMAND:  math.ceil(math.log2(len(self.demand_vars))) if binary else len(self.demand_vars),
            BDD.ET.PATH: max(1, math.ceil(math.log2(len(self.paths)))) if binary else len(self.paths),
            BDD.ET.LAMBDA: max(1, math.ceil(math.log2(wavelengths))) if binary else wavelengths,
            BDD.ET.SOURCE: math.ceil(math.log2(len(self.node_vars))) if binary else len(self.node_vars),
            BDD.ET.TARGET: math.ceil(math.log2(len(self.node_vars))) if binary else len(self.node_vars),
            
        }
        self.gen_vars(ordering, group_by_edge_order, interleave_lambda_binary_vars, generics_first)
     
    def gen_vars(self, ordering: list[ET], group_by_edge_order = False,  interleave_lambda_binary_vars = False, generic_first = False):
        
        for type in ordering:
            if type == BDD.ET.DEMAND:
                    self.declare_variables(BDD.ET.DEMAND)
                    self.declare_variables(BDD.ET.DEMAND, 2)
            elif type == BDD.ET.PATH:
                print(self.encoding_counts[BDD.ET.PATH])
                self.declare_generic_and_specific_variables(BDD.ET.PATH, [i for i in range(1, 1 + self.encoding_counts[BDD.ET.PATH])], group_by_edge_order, generic_first)
            elif type == BDD.ET.LAMBDA:
                self.declare_generic_and_specific_variables(BDD.ET.LAMBDA,  list(range(1, 1 + self.encoding_counts[BDD.ET.LAMBDA])), interleave_lambda_binary_vars, generic_first)
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

    def declare_generic_and_specific_variables(self, type: ET, l: list[int], group_by_edge_order=False, generic_first=False):
        bdd_vars = []

        def append(item, demand):
            bdd_vars.append(f"{BDD.prefixes[type]}{item}_{demand}")
            bdd_vars.append(f"{self.get_prefix_multiple(type,2)}{item}_{demand}")
        
        def gen_generics():
            for item in l:
                bdd_vars.append(f"{BDD.prefixes[type]}{item}")
                bdd_vars.append(f"{self.get_prefix_multiple(type,2)}{item}")
        
        if generic_first:
            gen_generics()
        
        if group_by_edge_order:
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
            return f"{BDD.prefixes[BDD.ET.PATH]}{edge}{f'_{demand}' if demand is not None else ''}"
        
        return f"{override}{edge}{f'_{demand}' if demand is not None else ''}"

    def get_p_vector(self, demand: int , override = None):
        l1 = []
        l2 = []
        for path in range(1,self.encoding_counts[BDD.ET.PATH]+1):
            l1.append(self.get_p_var(path, None, override))
            l2.append(self.get_p_var(path, demand, override))

        return self.make_subst_mapping(l1, l2)
    
    def get_lam_var(self, wavelength: int, demand = None, override = None):
        if override is  None:
            return f"{BDD.prefixes[BDD.ET.LAMBDA]}{wavelength}{f'_{demand}' if demand is not None else ''}"
        
        return f"{override}{wavelength}{f'_{demand}' if demand is not None else ''}"
        
    def get_lam_vector(self, demand: int, override = None):
        l1 = []
        l2 = []
        for wavelength in  range(1,self.encoding_counts[BDD.ET.LAMBDA]+1):
            l1.append(self.get_lam_var(wavelength, None, override))
            l2.append(self.get_lam_var(wavelength, demand, override))

        return self.make_subst_mapping(l1, l2)

    def get_index(self, item, type: ET):
        if type == BDD.ET.NODE:
            return self.node_vars[item]

        if type == BDD.ET.EDGE:
            return self.edge_vars[item]

        if type == BDD.ET.DEMAND:
            assert isinstance(item, int)
            return item

        return 0
    
    
    def encode(self, type: ET, number: int):
        if self.binary:
            return self.binary_encode(type, number)
        else:
            return self.unary_encode(type, number + 1)
        
    def unary_encode(self, type: ET, number: int):
        encoding_count = self.encoding_counts[type]
        encoding_expr = self.bdd.true
        for j in range(encoding_count):
            v = self.bdd.var(f"{BDD.prefixes[type]}{j+1}")
            if number != j+1:
                v = ~v 

            encoding_expr = encoding_expr & v
        
        return encoding_expr

    def binary_encode(self, type: ET, number: int):
        encoding_count = self.encoding_counts[type]
        encoding_expr = self.bdd.true
        for j in range(encoding_count):
            v = self.bdd.var(f"{BDD.prefixes[type]}{j+1}")
            if not (number >> (j)) & 1:
                v = ~v

            encoding_expr = encoding_expr & v
          
        return encoding_expr
    

    def get_prefix_multiple(self, type: ET, multiple: int):
        return "".join([BDD.prefixes[type] for _ in range(multiple)])

    def get_encoding_var_list(self, type: ET, override_prefix = None):
        return [f"{BDD.prefixes[type] if override_prefix is None else override_prefix}{i+1}" for i in range(self.encoding_counts[type])]

    def equals(self, e1: list[str], e2: list[str]):
        assert len(e1) == len(e2)

        expr = self.bdd.true
        for (var1, var2) in zip(e1,e2):
            s = (self.bdd.var(var1) & self.bdd.var(var2)) |(~self.bdd.var(var1) & ~self.bdd.var(var2))
            expr = expr & s

        return expr

class SourceBlock():
    def __init__(self, base: BDD):
        self.expr = base.bdd.false

        for i, demand in base.demand_vars.items():
            v_enc = base.encode(BDD.ET.NODE, base.get_index(demand.source, BDD.ET.NODE))
            d_enc = base.encode(BDD.ET.DEMAND, base.get_index(i, BDD.ET.DEMAND))
            self.expr = self.expr | (v_enc & d_enc)

class TargetBlock():
    def __init__(self, base: BDD):
        self.expr = base.bdd.false

        for i, demand in base.demand_vars.items():
            v_enc = base.encode(BDD.ET.NODE, base.get_index(demand.target, BDD.ET.NODE))
            d_enc = base.encode(BDD.ET.DEMAND, base.get_index(i, BDD.ET.DEMAND))
            self.expr = self.expr | (v_enc & d_enc)

class SingleWavelengthBlock():
    def __init__(self, base: BDD):
        self.expr = base.bdd.false
        for i in range(base.wavelengths):
            self.expr = self.expr | base.encode(BDD.ET.LAMBDA, i)

class OverlapsBlock():
    def __init__(self, base: BDD):
        l_list = base.get_encoding_var_list(BDD.ET.LAMBDA)
        ll_list =base.get_encoding_var_list(BDD.ET.LAMBDA, base.get_prefix_multiple(BDD.ET.LAMBDA, 2))
        
        d_list = base.get_encoding_var_list(BDD.ET.DEMAND)
        dd_list = base.get_encoding_var_list(BDD.ET.DEMAND, base.get_prefix_multiple(BDD.ET.DEMAND, 2))

        p_list = base.get_encoding_var_list(BDD.ET.PATH)
        pp_list = base.get_encoding_var_list(BDD.ET.PATH, base.get_prefix_multiple(BDD.ET.PATH, 2))
        
        self.expr = base.bdd.false
        
        for (i, j) in base.overlapping_paths:
            path1 = base.encode(BDD.ET.PATH, i)
            path2 = base.bdd.let(base.make_subst_mapping(p_list, pp_list), base.encode(base.ET.PATH, j))           
            self.expr |= (path1 & path2 & base.equals(l_list, ll_list) & ~base.equals(d_list, dd_list))
        
class FixedPathSimpleBlock():
    def __init__(self, paths, base: BDD):
        self.expr = base.bdd.false
        #print(paths)
        for i, path in enumerate(paths):
            s_expr = base.encode(BDD.ET.SOURCE, base.get_index(path[0][0], BDD.ET.NODE))
            t_expr = base.encode(BDD.ET.TARGET, base.get_index(path[-1][1], BDD.ET.NODE))
            path_expr = base.encode(BDD.ET.PATH, i)
            
            p_expr = (s_expr & t_expr & path_expr)

            self.expr |= p_expr
              
class DemandPathBlock():
    def __init__(self, path : FixedPathSimpleBlock, source : SourceBlock, target : TargetBlock, base: BDD):

        v_list = base.get_encoding_var_list(BDD.ET.NODE)
        s_list = base.get_encoding_var_list(BDD.ET.SOURCE)
        t_list = base.get_encoding_var_list(BDD.ET.TARGET)

        source_subst = base.bdd.let(base.make_subst_mapping(v_list, s_list), source.expr)
        target_subst = base.bdd.let(base.make_subst_mapping(v_list, t_list), target.expr)

        self.expr = (path.expr & source_subst & target_subst).exist(*s_list + t_list)
        

class RoutingAndWavelengthBlock():
    def __init__(self, demandPath : DemandPathBlock, wavelength: SingleWavelengthBlock, base: BDD, constrained=False):

        d_list = base.get_encoding_var_list(BDD.ET.DEMAND)
        l_list = base.get_encoding_var_list(BDD.ET.LAMBDA)
        
        self.expr = base.bdd.true

        for i in base.demand_vars.keys():
            
            wavelength_subst = base.bdd.false
            
            if constrained:
                for w in range(min(base.wavelengths, i+1)):
                    wavelength_subst |= base.bdd.let(base.get_lam_vector(i),base.encode(BDD.ET.LAMBDA, w))
            else:
                wavelength_subst = base.bdd.let(base.get_lam_vector(i),wavelength.expr)

            demandPath_subst = base.bdd.let(base.get_p_vector(i),demandPath.expr)
            #print(get_assignments(base.bdd, demandPath_subst))
            #exit()
            
            self.expr = (self.expr & (demandPath_subst & wavelength_subst & base.encode(base.ET.DEMAND, i)).exist(*(d_list+l_list)))

    def assignment_to_expr(self, assignment: dict[str, bool], base: BDD):
        expr = base.bdd.true
        for k,v in assignment.items():
            expr &= base.bdd.var(k) if v else ~base.bdd.var(k)
        
        return expr
    
    def identify_lambdas(self, assignment: dict[str, bool], base: BDD):
        def power(l_var: str):
            val = int(l_var.replace(base.prefixes[BDD.ET.LAMBDA], ""))
            return 2 ** (base.encoding_counts[BDD.ET.LAMBDA] - val)
        
        colors = {str(k):0 for k in base.demand_vars.keys()}

        for k, v in assignment.items():     
            if k[0] == base.prefixes[BDD.ET.LAMBDA] and v:
                [l_var, demand_id] = k.split("_")
                colors[demand_id] += power(l_var)

        return colors 
        
    def transform(self, assignment: dict[str, int], base: BDD):
        lambdas = set(list(assignment.values()))
        transformations = []
        perms = permutations(range(base.wavelengths), len(lambdas))
        for p in  permutations(range(base.wavelengths), len(lambdas)):
            transformations.append({k:p[i] for i, k in enumerate(lambdas)})

        return transformations

class SequenceWavelengthsBlock():
    def __init__(self, rwa_block: RoutingAndWavelengthBlock, base: BDD):
        self.expr = rwa_block.expr
        
        demand_lambda_substs = {d: base.get_lam_vector(d) for d in base.demand_vars}
        
        for l in range(1, base.wavelengths):
            u = base.bdd.false
            v = base.bdd.false
            for d in base.demand_vars:
                u |= base.bdd.let(demand_lambda_substs[d], base.encode(base.ET.LAMBDA, l))
                
                if d < l:
                    v |= base.bdd.let(demand_lambda_substs[d], base.encode(base.ET.LAMBDA, l-1))

            self.expr &= u.implies(v)
        
                
class FullNoClashBlock():
    def __init__(self,  rwa: Function, overlap : OverlapsBlock, wavelength: SingleWavelengthBlock, base: BDD):
        self.expr = rwa
        d_list = base.get_encoding_var_list(BDD.ET.DEMAND)
        dd_list = base.get_encoding_var_list(BDD.ET.DEMAND, base.get_prefix_multiple(BDD.ET.DEMAND, 2))
        pp_list = base.get_encoding_var_list(BDD.ET.PATH, base.get_prefix_multiple(BDD.ET.PATH, 2))
        l_list = base.get_encoding_var_list(BDD.ET.LAMBDA)
        ll_list = base.get_encoding_var_list(BDD.ET.LAMBDA, base.get_prefix_multiple(BDD.ET.LAMBDA, 2))
        
        d_expr = []

        for i in base.demand_vars.keys():
            noClash_subst = base.bdd.true

            for j in base.demand_vars.keys():
                subst = {}
                
                subst.update(base.get_p_vector(i))
                subst.update(base.make_subst_mapping(pp_list, list(base.get_p_vector(j).values())))

                subst.update(base.get_lam_vector(i))
                subst.update(base.make_subst_mapping(ll_list, list(base.get_lam_vector(j).values())))
                
                d1 = base.encode(base.ET.DEMAND, i)
                d2 = base.bdd.let(base.make_subst_mapping(d_list, dd_list), base.encode(base.ET.DEMAND, j))
                
                noClash_subst = ~(base.bdd.let(subst, overlap.expr)) & d1 & d2
                d_expr.append(noClash_subst.exist(*(d_list + dd_list)))
        
        i_l = 0

        for j in range(i_l, len(d_expr)):
            
            # print(f"{j}/{len(d_expr)}")
            d_e = d_expr[j] 
            self.expr = self.expr & d_e

class OnlyOptimalBlock(): 
    def __init__(self,  rwa: Function, base: BDD):
        l = 1        
        rww =  base.bdd.false
        while (rww == base.bdd.false and l <= base.wavelengths):
            outer_expr = base.bdd.true
            for d in base.demand_vars: 
                d_expr = base.bdd.false

                for w in range(min(l, base.wavelengths)):
                    d_expr |= base.bdd.let(base.get_lam_vector(d),base.encode(BDD.ET.LAMBDA, w))
                outer_expr &= d_expr

            rww = rwa & outer_expr
            l += 1

        self.expr = rww
            

class RWAProblem:
    def __init__(self, G: MultiDiGraph, demands: dict[int, Demand], paths, overlapping_paths, ordering: list[BDD.ET], wavelengths: int, group_by_edge_order = False, interleave_lambda_binary_vars=False, generics_first = False, with_sequence = False, wavelength_constrained=False, binary=True, reordering=False, only_optimal=False):
        s = time.perf_counter()
        self.base = BDD(G, demands, ordering, paths, overlapping_paths, wavelengths, group_by_edge_order, interleave_lambda_binary_vars, generics_first, binary, reordering)

        source = SourceBlock(self.base)
        target = TargetBlock( self.base)
        print("Building path BDD...")
        before_path = time.perf_counter()
        
        ######### NEW #########
        path = FixedPathSimpleBlock(paths, self.base)
        overlap = OverlapsBlock(self.base)
        
        after_path = time.perf_counter()
        print(after_path - s,after_path - before_path, "Path built", flush=True)
        demandPath = DemandPathBlock(path, source, target, self.base)
        singleWavelength_expr = SingleWavelengthBlock(self.base)
                
        rwa = RoutingAndWavelengthBlock(demandPath, singleWavelength_expr, self.base, constrained=wavelength_constrained)
        
        e1 = time.perf_counter()
        print(e1 - s, e1-s, "Blocks",  flush=True)

        sequenceWavelengths = self.base.bdd.true
        if with_sequence:
            sequenceWavelengths = SequenceWavelengthsBlock(rwa, self.base)
        
        e2 = time.perf_counter()
        print(e2 - s, e2-e1, "Sequence", flush=True)
        
        full = rwa.expr 
        if with_sequence:
            full = full & sequenceWavelengths.expr

        e3 = time.perf_counter()

        fullNoClash = FullNoClashBlock(full, overlap, singleWavelength_expr, self.base)
        self.rwa = fullNoClash.expr
        e4 = time.perf_counter()
        print(e4 - s, e4 - e3, "FullNoClash", flush=True)
        print("")

        if only_optimal:
            e5 = time.perf_counter() 
            only_optimal = OnlyOptimalBlock(self.rwa, self.base)
            self.rwa = only_optimal.expr
            e6 = time.perf_counter()
            print(e6 - s, e6 - e5, "OnlyOptimal", flush=True)

    def get_assignments(self, amount):
        assignments = []
        
        for a in self.base.bdd.pick_iter(self.rwa):
            
            if len(assignments) == amount:
                return assignments

            assignments.append(a)
        
        return assignments    
        
    
    def print_assignments(self, true_only=False, keep_false_prefix=""):
        pretty_print(self.base.bdd, self.rwa, true_only, keep_false_prefix=keep_false_prefix)
 