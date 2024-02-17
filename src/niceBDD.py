  
from enum import Enum
import time

has_cudd = False

try:
    # raise ImportError()
    from dd.cudd import BDD as _BDD
    from dd.cudd import Function
    from dd.cudd import and_exists
    has_cudd = True
except ImportError:
   from dd.autoref import BDD as _BDD
   from dd.autoref import Function 
   print("Using autoref... ")

from networkx import MultiDiGraph
import math
from demands import Demand


def get_assignments(bdd: _BDD, expr):
    return list(bdd.pick_iter(expr))

def pretty_print(bdd: _BDD, expr, true_only=False, keep_false_prefix=""):
    ass: list[dict[str, bool]] = get_assignments(bdd, expr)
    for a in ass:         
        if true_only:
            a = {k:v for k,v in a.items() if v or k[0] == keep_false_prefix}
        print(dict(sorted(a.items())))


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


class BaseBDD:
   
    
    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand],  wavelengths, ordering: list[ET], group_by_edge_order = True, interleave_lambda_binary_vars=True, generics_first = True, binary=True, reordering=True, paths=[]):
        self.bdd = _BDD()
        self.topology = topology
        self.ordering = ordering
        self.reordering = reordering
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
        self.encoding_counts = {}
        self.demand_vars = demands
        self.encoded_node_vars :list[str]= []
        self.encoded_source_vars :list[str]= []
        self.encoded_target_vars :list[str]= []
        self.wavelengths = wavelengths
    
    def get_index(self, item, type: ET):
        if type == ET.NODE:
            return self.node_vars[item]

        if type == ET.EDGE:
            return self.edge_vars[item]

        if type == ET.DEMAND:
            assert isinstance(item, int)
            return item

        return 0
    
    def make_subst_mapping(self, l1: list[str], l2: list[str]):
        return {l1_e: l2_e for (l1_e, l2_e) in zip(l1, l2)}


    def equals(self, e1: list[str], e2: list[str]):
        assert len(e1) == len(e2)

        expr = self.bdd.true
        for (var1, var2) in zip(e1,e2):
            s = (self.bdd.var(var1) & self.bdd.var(var2)) |(~self.bdd.var(var1) & ~self.bdd.var(var2))
            expr = expr & s

        return expr

    
    def encode(self, type: ET, number: int):
        encoding_count = self.encoding_counts[type]
        encoding_expr = self.bdd.true
        for j in range(encoding_count):
            v = self.bdd.var(f"{prefixes[type]}{j+1}")
            if not (number >> (j)) & 1:
                v = ~v

            encoding_expr = encoding_expr & v
          
        return encoding_expr
    
    
    def get_p_var(self, edge: int, demand =  None, override = None):
        if override is None:
            return f"{prefixes[ET.PATH]}{edge}{f'_{demand}' if demand is not None else ''}"
        
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
            return f"{prefixes[ET.LAMBDA]}{wavelength}{f'_{demand}' if demand is not None else ''}"
        
        return f"{override}{wavelength}{f'_{demand}' if demand is not None else ''}"
        
    def get_lam_vector(self, demand: int, override = None):
        l1 = []
        l2 = []
        for wavelength in  range(1,self.encoding_counts[ET.LAMBDA]+1):
            l1.append(self.get_lam_var(wavelength, None, override))
            l2.append(self.get_lam_var(wavelength, demand, override))

        return self.make_subst_mapping(l1, l2)

    def get_prefix_multiple(self, type: ET, multiple: int):
        return "".join([prefixes[type] for _ in range(multiple)])

    def get_encoding_var_list(self, type: ET, override_prefix = None):
        offset = 0
        if type == ET.PATH:
            offset = 1

        return [f"{prefixes[type] if override_prefix is None else override_prefix}{i+1 - offset}" for i in range(self.encoding_counts[type])]

    
    def gen_vars(self, ordering: list[ET], group_by_edge_order = False,  interleave_lambda_binary_vars = False, generic_first = False):
        
        for type in ordering:
            if type == ET.DEMAND:
                self.declare_variables(ET.DEMAND)
                self.declare_variables(ET.DEMAND, 2)
            elif type == ET.PATH:
                self.declare_generic_and_specific_variables(ET.PATH, list(self.edge_vars.values()), group_by_edge_order, generic_first)
            elif type == ET.LAMBDA:
                self.declare_generic_and_specific_variables(ET.LAMBDA,  list(range(1, 1 + self.encoding_counts[ET.LAMBDA])), interleave_lambda_binary_vars, generic_first)
            elif type == ET.EDGE:
                self.declare_variables(ET.EDGE)
                self.declare_variables(ET.EDGE, 2)
            
            elif type in [ET.NODE,ET.SOURCE,ET.TARGET]:
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
            bdd_vars.append(f"{prefixes[type]}{item}_{demand}")
            bdd_vars.append(f"{self.get_prefix_multiple(type,2)}{item}_{demand}")
        
        def gen_generics():
            for item in l:
                bdd_vars.append(f"{prefixes[type]}{item}")
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

class DefaultBDD(BaseBDD):
    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand], ordering: list[ET], wavelengths = 2, group_by_edge_order = True, interleave_lambda_binary_vars=True, generics_first = True, binary=True, reordering=True, paths=[]):
        super().__init__(topology, demands, wavelengths, ordering, group_by_edge_order, interleave_lambda_binary_vars, generics_first, binary, reordering, paths)
        
        self.demand_vars = demands
        self.paths = paths
                
        self.encoding_counts = {
            ET.NODE: math.ceil(math.log2(len(self.node_vars))),
            ET.EDGE:  math.ceil(math.log2(len(self.edge_vars))),
            ET.DEMAND:  math.ceil(math.log2(len(self.demand_vars))),
            ET.PATH: len(self.edge_vars),
            ET.LAMBDA: max(1, math.ceil(math.log2(wavelengths))),
            ET.SOURCE: math.ceil(math.log2(len(self.node_vars))),
            ET.TARGET: math.ceil(math.log2(len(self.node_vars))),
        }
        self.gen_vars(ordering, group_by_edge_order, interleave_lambda_binary_vars, generics_first)
     
class DynamicBDD(BaseBDD):

    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand], ordering: list[ET], wavelengths: int = 2, group_by_edge_order:bool = False, interleave_lambda_binary_vars=False, generics_first:bool = False, init_demand=0, max_demands=128, reordering=True):
        super().__init__(topology, demands, wavelengths, ordering, group_by_edge_order, interleave_lambda_binary_vars, generics_first, reordering)

        self.demand_vars = {(init_demand+i):d for i,d in enumerate(demands.values())}
                
        self.encoding_counts = {
            ET.NODE: math.ceil(math.log2(len(self.node_vars.keys()))),
            ET.EDGE:  math.ceil(math.log2(len(self.edge_vars.keys()))),
            ET.DEMAND:  max(1, math.ceil(math.log2(max_demands))),
            ET.PATH: len(self.edge_vars.keys()),
            ET.LAMBDA: max(1, math.ceil(math.log2(wavelengths))),
            ET.SOURCE: math.ceil(math.log2(len(self.node_vars.keys()))),
            ET.TARGET: math.ceil(math.log2(len(self.node_vars.keys()))),

        }
        self.bdd.configure(reordering=False)
        self.gen_vars(ordering, group_by_edge_order, interleave_lambda_binary_vars, generics_first)

class EncodedPathBDD(BaseBDD):
    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand], ordering: list[ET], paths, overlapping_paths, wavelengths = 2, group_by_edge_order = True, interleave_lambda_binary_vars=True, generics_first = True, binary=True, reordering=False):
        super().__init__(topology, demands, wavelengths, ordering, group_by_edge_order, interleave_lambda_binary_vars, generics_first, reordering)
        
        self.paths = paths
        self.overlapping_paths = overlapping_paths
        self.overlapping_demands = {}
        
        for (path1, path2) in overlapping_paths:
            if path1 == path2:
                continue
            self.overlapping_demands[(path1, path2)] = [demand_id for demand_id, demand in self.demand_vars.items() if (paths[path1][0][0] == demand.source and paths[path1][-1][1] == demand.target) or (paths[path2][0][0] == demand.source and paths[path2][-1][1] == demand.target)]

        self.encoding_counts = {
            ET.NODE: math.ceil(math.log2(len(self.node_vars))),
            ET.EDGE:  math.ceil(math.log2(len(self.edge_vars))),
            ET.DEMAND:  math.ceil(math.log2(len(self.demand_vars))),
            ET.PATH: max(1, math.ceil(math.log2(len(self.paths)))),
            ET.LAMBDA: max(1, math.ceil(math.log2(wavelengths))),
            ET.SOURCE: math.ceil(math.log2(len(self.node_vars))),
            ET.TARGET: math.ceil(math.log2(len(self.node_vars))),
            
        }
        self.gen_vars(ordering, group_by_edge_order, interleave_lambda_binary_vars, generics_first)
     
    def gen_vars(self, ordering: list[ET], group_by_edge_order = False,  interleave_lambda_binary_vars = False, generic_first = False):
        
        for type in ordering:
            if type == ET.DEMAND:
                self.declare_variables(ET.DEMAND)
                self.declare_variables(ET.DEMAND, 2)
            elif type == ET.PATH:
                self.declare_generic_and_specific_variables(ET.PATH, [i for i in range(1, 1 + self.encoding_counts[ET.PATH])], group_by_edge_order, generic_first)
            elif type == ET.LAMBDA:
                self.declare_generic_and_specific_variables(ET.LAMBDA,  list(range(1, 1 + self.encoding_counts[ET.LAMBDA])), interleave_lambda_binary_vars, generic_first)
            elif type == ET.EDGE:
                self.declare_variables(ET.EDGE)
                self.declare_variables(ET.EDGE, 2)
            elif type in [ET.NODE,ET.SOURCE,ET.TARGET]:
                self.declare_variables(type)
            else: 
                raise Exception(f"Error: the given type {type} did not match any BDD type.")
    
    def get_p_vector(self, demand: int , override = None):
        l1 = []
        l2 = []
        for path in range(1,self.encoding_counts[ET.PATH]+1):
            l1.append(self.get_p_var(path, None, override))
            l2.append(self.get_p_var(path, demand, override))

        return self.make_subst_mapping(l1, l2)
    
    def get_encoding_var_list(self, type: ET, override_prefix = None):
        return [f"{prefixes[type] if override_prefix is None else override_prefix}{i+1}" for i in range(self.encoding_counts[type])]
    
class SplitBDD(BaseBDD):
    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand], ordering: list[ET], 
                wavelengths = 2, group_by_edge_order = True, interleave_lambda_binary_vars=True, 
                generics_first = True, binary=True, reordering=False):
        
        super().__init__(topology, demands, wavelengths, ordering, group_by_edge_order, interleave_lambda_binary_vars, generics_first, reordering)
        
        self.node_vars = {n: nId[1] for n, nId in zip(topology.nodes, topology.nodes(data=("id")))} 
        self.edge_vars = {e: eId[2] for e, eId in zip(topology.edges(keys=True), topology.edges(data=("id")))}

        self.encoding_counts = {
            ET.NODE: math.ceil(math.log2(1+(max([i for n, i in self.node_vars.items()])))),
            ET.EDGE:  math.ceil(math.log2(1+(max([i for e, i in self.edge_vars.items()])))), 
            ET.DEMAND:  math.ceil(math.log2(max(max(max([i for i, d in self.demand_vars.items()]), len(self.demand_vars)), 2))),
            ET.PATH:   1+(max([i for e, i in self.edge_vars.items()])),
            ET.LAMBDA: max(1, math.ceil(math.log2(wavelengths))),
            ET.SOURCE: math.ceil(math.log2(1+(max([i for n, i in self.node_vars.items()])))),
            ET.TARGET: math.ceil(math.log2(1+(max([i for n, i in self.node_vars.items()])))),
        }
        self.gen_vars(ordering, group_by_edge_order, interleave_lambda_binary_vars, generics_first)
    
    def gen_vars(self, ordering: list[ET], group_by_edge_order = False,  interleave_lambda_binary_vars = False, generic_first = False):
        
        for type in ordering:
            if type == ET.DEMAND:
                    self.declare_variables(ET.DEMAND)
                    self.declare_variables(ET.DEMAND, 2)
            elif type == ET.PATH:
                    self.declare_generic_and_specific_variables(ET.PATH, list(self.edge_vars.values()), group_by_edge_order, generic_first)
            elif type == ET.LAMBDA:
                self.declare_generic_and_specific_variables(ET.LAMBDA,  list(range(1, 1 + self.encoding_counts[ET.LAMBDA])), interleave_lambda_binary_vars, generic_first)
            elif type == ET.EDGE:
                self.declare_variables(ET.EDGE)
                self.declare_variables(ET.EDGE, 2)
            
            elif type in [ET.NODE,ET.SOURCE,ET.TARGET]:
                self.declare_variables(type)
            else: 
                raise Exception(f"Error: the given type {type} did not match any BDD type.")

    def get_encoding_var_list(self, type: ET, override_prefix = None):
        offset = 0
        if type == ET.PATH:
            offset = 1
            ls = []
            for e, i in self.edge_vars.items(): 
                ls.append(f"{prefixes[type] if override_prefix is None else override_prefix}{i+1 - offset}")
            return ls
        return [f"{prefixes[type] if override_prefix is None else override_prefix}{i+1 - offset}" for i in range(self.encoding_counts[type])]