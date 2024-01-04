
from enum import Enum
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
from bdd import *



class DynamicBDD(BDD):

    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand], ordering: list[BDD.ET], wavelengths: int = 2, group_by_edge_order:bool = False, generics_first:bool = False, init_demand=0, max_demands=128, binary=True):
        self.bdd = _BDD()
        if has_cudd:
            print("Has cudd")
            self.bdd.configure(
                # number of bytes
                max_memory=50 * (2**30),
                reordering=False)
        else:
            self.bdd.configure(reordering=False)
            
        self.G=topology
        self.ordering=ordering
        self.group_by_edge_order=group_by_edge_order
        self.generics_first=generics_first

        self.variables = []
        self.node_vars = {v:i for i,v in enumerate(topology.nodes)}
        self.edge_vars = {e:i for i,e in enumerate(topology.edges)} 
        self.demand_vars = {(init_demand+i):d for i,d in enumerate(demands.values())}
        self.encoded_node_vars :list[str]= []
        self.encoded_source_vars :list[str]= []
        self.encoded_target_vars :list[str]= []
        self.wavelengths = wavelengths
        self.init_demand=init_demand
        self.binary = binary
                
        self.encoding_counts = {
            BDD.ET.NODE: math.ceil(math.log2(len(self.node_vars.keys()))),
            BDD.ET.EDGE:  math.ceil(math.log2(len(self.edge_vars.keys()))),
            BDD.ET.DEMAND:  max(1, math.ceil(math.log2(max_demands))),
            BDD.ET.PATH: len(self.edge_vars.keys()),
            BDD.ET.LAMBDA: max(1, math.ceil(math.log2(wavelengths))),
            BDD.ET.SOURCE: math.ceil(math.log2(len(self.node_vars.keys()))),
            BDD.ET.TARGET: math.ceil(math.log2(len(self.node_vars.keys()))),

        }
        self.bdd.configure(reordering=False)
        self.gen_vars(ordering, group_by_edge_order, generics_first)

    
    # Demands, Paths, Lambdas, Edges, Nodes (T, N, S)
    def gen_vars(self, ordering: list[BDD.ET], group_by_edge_order: bool = False, generic_first:bool = False):
        for type in ordering:
            if type == BDD.ET.DEMAND:
                    self.declare_variables(BDD.ET.DEMAND)
                    self.declare_variables(BDD.ET.DEMAND, 2)
            elif type == BDD.ET.PATH:
                    self.declare_generic_and_specific_variables(BDD.ET.PATH, list(self.edge_vars.values()), group_by_edge_order, generic_first)
            elif type == BDD.ET.LAMBDA:
                self.declare_generic_and_specific_variables(BDD.ET.LAMBDA,  list(range(1, 1 + self.encoding_counts[BDD.ET.LAMBDA])), group_by_edge_order, generic_first)
            elif type == BDD.ET.EDGE:
                self.declare_variables(BDD.ET.EDGE)
                self.declare_variables(BDD.ET.EDGE, 2)
            
            elif type in [BDD.ET.NODE,BDD.ET.SOURCE,BDD.ET.TARGET]:
                self.declare_variables(type)
            else: 
                raise Exception(f"Error: the given type {type} did not match any BDD type.")
                    
    def declare_variables(self, type: BDD.ET, prefix_count: int = 1):
        d_bdd_vars = [f"{self.get_prefix_multiple(type, prefix_count)}{self.encoding_counts[type] - i}" for i in range(0,self.encoding_counts[type])]
        self.bdd.declare(*d_bdd_vars)
        
        return d_bdd_vars
        

    def declare_generic_and_specific_variables(self, type: BDD.ET, l: list[int], group_by_edge_order=False, generic_first=False):
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
        for edge in  self.edge_vars.values():
            l1.append(self.get_p_var(edge, None, override))
            l2.append(self.get_p_var(edge, demand, override))

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


    def compile(self):
        return self.bdd

    def get_index(self, item, type: BDD.ET):
        if type == BDD.ET.NODE:
            return self.node_vars[item]

        if type == BDD.ET.EDGE:
            return self.edge_vars[item]

        if type == BDD.ET.DEMAND:
            assert isinstance(item, int)
            return item

        return 0
    
    

    def binary_encode(self, type: BDD.ET, number: int):
        encoding_count = self.encoding_counts[type]
        encoding_expr = self.bdd.true
        for j in range(encoding_count):
            v = self.bdd.var(f"{BDD.prefixes[type]}{j+1}")
            if not (number >> (j)) & 1:
                v = ~v

            encoding_expr = encoding_expr & v
          
        return encoding_expr

    def get_prefix_multiple(self, type: BDD.ET, multiple: int):
        return "".join([BDD.prefixes[type] for _ in range(multiple)])

    def get_encoding_var_list(self, type: BDD.ET, override_prefix = None):
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



   
class DynamicFullNoClash():
    def __init__(self, demands1: dict[int,Demand], demands2: dict[int,Demand], noClash: NoClashBlock, base: DynamicBDD, init: Function):
        self.expr = init
        d_list = base.get_encoding_var_list(BDD.ET.DEMAND)
        dd_list = base.get_encoding_var_list(BDD.ET.DEMAND, base.get_prefix_multiple(BDD.ET.DEMAND, 2))
        pp_list = base.get_encoding_var_list(BDD.ET.PATH, base.get_prefix_multiple(BDD.ET.PATH, 2))
        ll_list = base.get_encoding_var_list(BDD.ET.LAMBDA, base.get_prefix_multiple(BDD.ET.LAMBDA, 2))
        
        d_expr = []


        for i in demands1.keys():
            noClash_subst = base.bdd.true

            for j in demands2.keys():

                subst = {}
                subst.update(base.get_p_vector(i))
                subst.update(base.make_subst_mapping(pp_list, list(base.get_p_vector(j).values())))

                subst.update(base.get_lam_vector(i))
                subst.update(base.make_subst_mapping(ll_list, list(base.get_lam_vector(j).values())))
                noClash_subst = base.bdd.let(subst, noClash.expr) & base.binary_encode(base.ET.DEMAND, i) & base.bdd.let(base.make_subst_mapping(d_list, dd_list), base.binary_encode(base.ET.DEMAND, j)) 
                d_expr.append(noClash_subst.exist(*(d_list + dd_list)))
        
        i_l = 0
        # for i in range(0, len(d_expr),3):
        #     i_l = i
        #     if i > len(d_expr) - 3:
        #         break
            
            
        #     # print(f"{i}/{len(d_expr)}")
        #     d_e1 = d_expr[i]
        #     d_e2 = d_expr[i+1]
        #     d_e3 = d_expr[i+2]
        #     d_e = d_e1 & d_e2 & d_e3 
        #     self.expr = self.expr & d_e   

        
        for j in range(i_l, len(d_expr)):
            
            # print(f"{j}/{len(d_expr)}")
            d_e = d_expr[j] 
            self.expr = self.expr & d_e


                         

class DynamicRWAProblem:
    def __init__(self, G: MultiDiGraph, demands: dict[int, Demand], ordering: list[BDD.ET], wavelengths: int, group_by_edge_order = True, generics_first = True, with_sequence = False, wavelength_constrained=False, init_demand=0):
        s = time.perf_counter()
        self.base = DynamicBDD(G, demands, ordering, wavelengths, group_by_edge_order, generics_first, init_demand)
       
        in_expr = InBlock(G, self.base)
        out_expr = OutBlock(G, self.base)
        source = SourceBlock(self.base)
        target = TargetBlock( self.base)
        trivial_expr = TrivialBlock(G, self.base)
        passes = PassesBlock(G, self.base)
        singleOut = SingleOutBlock(out_expr, passes, self.base)
        changed = ChangedBlock(passes, self.base)
        print("Building path BDD...")
        before_path = time.perf_counter()
        path = PathBlock(trivial_expr, out_expr,in_expr, changed, singleOut, self.base)
        after_path = time.perf_counter()
        print("Total: ",after_path - s, "Path built: ",after_path - before_path)
        demandPath = DemandPathBlock(path,source,target,self.base)
        singleWavelength_expr = SingleWavelengthBlock(self.base)
        noClash_expr = NoClashBlock(passes, self.base) 
        
        rwa = RoutingAndWavelengthBlock(demandPath, singleWavelength_expr, self.base, constrained=wavelength_constrained)
        
        e1 = time.perf_counter()
        print(e1 - s, e1-s, "Blocks",  flush=True)

        sequenceWavelengths = self.base.bdd.true
        if with_sequence:
            sequenceWavelengths = SequenceWavelengthsBlock(rwa, self.base)
        
        # simplified = SimplifiedRoutingAndWavelengthBlock(rwa.expr & sequenceWavelengths.expr, self.base)
        
        #print(rwa.expr.count())
        # print((rwa.expr & sequenceWavelengths.expr).count())
        #print((sequenceWavelengths.expr).count())
        
        e2 = time.perf_counter()
        print(e2 - s, e2-e1, "Sequence", flush=True)
        full = rwa.expr #& sequenceWavelengths.expr
        
        if with_sequence:
            full = full & sequenceWavelengths.expr
            
        e3 = time.perf_counter()
       # print(e3 - s, e3-e2, "Simplify",flush=True)

        fullNoClash = FullNoClashBlock(rwa.expr, noClash_expr, self.base)
        self.expr = fullNoClash.expr
        e4 = time.perf_counter()
        print(e4 - s, e4 - e3, "FullNoClash", flush=True)
        print("")
        

    
    def get_assignments(self, amount):
        assignments = []
        
        for a in self.base.bdd.pick_iter(self.expr):
            
            if len(assignments) == amount:
                return assignments

            assignments.append(a)
        
        return assignments    
        
    
    def print_assignments(self, true_only=False, keep_false_prefix=""):
        pretty_print(self.base.bdd, self.expr, true_only, keep_false_prefix=keep_false_prefix)
        
class AddBlock():
    def __init__(self, rwa1, rwa2):
        if not rwa1.base.G == rwa2.base.G:
            raise ValueError("Topologies not equal")
        if not rwa1.base.wavelengths == rwa2.base.wavelengths:
            raise ValueError("Wavelengths not equal")
        if  max([0] + list(rwa1.base.demand_vars.keys())) != (min(list(rwa2.base.demand_vars.keys()))-1):
            print(rwa1.base.demand_vars)
            print(rwa2.base.demand_vars)
            raise ValueError("Demands keys are not directly sequential")

        demands = {}
        demands.update(rwa1.base.demand_vars)
        demands.update(rwa2.base.demand_vars)

        self.base = DynamicBDD(rwa1.base.G,demands, rwa1.base.ordering, rwa1.base.wavelengths, rwa1.base.group_by_edge_order, rwa1.base.generics_first,min(list(rwa1.base.demand_vars.keys())))
        old_assignments = rwa1.base.bdd.copy(rwa1.expr, self.base.bdd)
        
        new_assignments = rwa2.base.bdd.copy(rwa2.expr, self.base.bdd)

        passes=PassesBlock(rwa1.base.G,self.base)
        noclash=NoClashBlock(passes, self.base)

        dynamicNoClash = DynamicFullNoClash(rwa1.base.demand_vars, rwa2.base.demand_vars, noclash, self.base, old_assignments & new_assignments)

        self.expr = (dynamicNoClash.expr)
        
if __name__ == "__main__":
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/four_node.dot"))

    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
        
    demands = {
                0: Demand("A", "B"), 
                1: Demand("B", "D"), 
               }
    demands2 = {2: Demand("C","D"), 3: Demand("D","A")}
    
    all_demands = {
               0: Demand("A", "B"), 
               1: Demand("B", "D"), 
               2: Demand("A", "B"), 
               3: Demand("B", "D"), 
               4: Demand("A", "B"), 
               5: Demand("B", "D"), 
               }
    


    types = [BDD.ET.LAMBDA,BDD.ET.DEMAND,BDD.ET.PATH,BDD.ET.EDGE,BDD.ET.SOURCE,BDD.ET.TARGET,BDD.ET.NODE]
    w=2


    rw1 = DynamicRWAProblem(G, demands, types, w, group_by_edge_order =True, generics_first=False, init_demand=0)
    rw2 = DynamicRWAProblem(G, demands2, types, w, group_by_edge_order =True, generics_first=False, init_demand=len(rw1.base.demand_vars.keys()))
    
    add=AddBlock(rw1,rw2)
