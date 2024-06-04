from enum import Enum
import time
import traceback

has_cudd = False
try:
    # raise ImportError()
    from dd.cudd import BDD as _BDD
    has_cudd = True
except ImportError:
   from dd.autoref import BDD as _BDD
   print("Using autoref... ")

from networkx import MultiDiGraph
import math
from demands import Demand
from topology import d_to_legal_path_dict, get_overlap_graph
import topology 

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
    PATH=5
    SOURCE=6
    TARGET=7
    CHANNEL=8
        
prefixes = {
    ET.NODE: "v",
    ET.EDGE: "e",
    ET.DEMAND: "d",
    ET.PATH: "p",
    ET.SOURCE: "s", 
    ET.TARGET: "t", 
    ET.CHANNEL: "c"
}

class ChannelData:
    
    def __init__(self, demands, slots, use_lim=False, cliques=[], clique_limit=False, sub_spectrum=False, buckets=[], safe_lim=False):
        self.input = (demands, slots, use_lim, cliques, clique_limit, sub_spectrum, buckets)
        self.channels = topology.get_channels(demands, number_of_slots=slots, limit=use_lim, cliques=cliques, clique_limit=clique_limit, safe_limit=safe_lim)          
        self.splits = buckets
        
        if sub_spectrum:
            interval = math.ceil(slots / len(self.splits))
            self.channels = {}
            
            for i, s in enumerate(self.splits):
                s_channels = topology.get_channels({k:v for k, v in demands.items() if k in s}, number_of_slots=slots, limit=use_lim, cliques=cliques, clique_limit=clique_limit)
                for d, cs in s_channels.items():
                    new_channels = []
                    for c in cs: 
                        new_channel = [s+(i)*interval for s in c]
                        if new_channel[-1] < slots and new_channel[0] >= i * interval and new_channel[-1] < (i+1)*interval:
                            new_channels.append(new_channel)

                    self.channels[d] = new_channels
  
        self.overlapping_channels, self.unique_channels = topology.get_overlapping_channels(self.channels)
        self.connected_channels = topology.get_connected_channels(self.unique_channels)
        self.non_overlapping_channels = set([(i,j) for i,_ in enumerate(self.unique_channels) for j,_ in enumerate(self.unique_channels)]) - set(self.overlapping_channels)

class BaseBDD:
    
    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand],  
                 channel_data:ChannelData,
                 ordering: list[ET], reordering=True, 
                 paths=[],overlapping_paths = [], failover=0
                ):
        
        self.bdd = _BDD()
        self.topology = topology
        self.reordering = reordering
        self.ordering = ordering
        self.max_failovers = failover
        if has_cudd:
            print("Has cudd")
            self.bdd.configure(
                # number of bytes
                max_memory=50 * (2**30),
                reordering=reordering,
                )
        else:
            self.bdd.configure(reordering=reordering)

        self.variables = []
        self.channel_data = channel_data
        self.demand_to_channels = channel_data.channels 
        self.unique_channels = channel_data.unique_channels
        self.overlapping_channels = channel_data.overlapping_channels
        self.connected_channels = channel_data.connected_channels
        self.non_overlapping_channels = channel_data.non_overlapping_channels 

        self.demand_vars = demands
        
        self.edge_vars = {e:i for i,e in enumerate(topology.edges(keys=True))} 
        self.node_vars = {v:i for i,v in enumerate(topology.nodes)}
            
        self.paths = paths

        self.d_to_paths = d_to_legal_path_dict(demands, paths) # May not work ...

        self.overlapping_paths = overlapping_paths
        self.non_overlapping_paths = set([(i,j) for i,_ in enumerate(self.paths) for j,_ in enumerate(self.paths)]) - set(self.overlapping_paths)

        overlap,_ = get_overlap_graph(self.demand_vars,self.paths)
        self.potential_overlap_graph = overlap

        self.encoding_counts = {
            ET.EDGE: 0,
            ET.NODE: math.ceil(math.log2(len(self.node_vars))),
            ET.DEMAND:  math.ceil(math.log2(len(self.demand_vars))),
            ET.CHANNEL:  max(1, math.ceil(math.log2(len(self.unique_channels)))),
            ET.PATH:  max(1, math.ceil(math.log2(len(self.paths)))),
            ET.SOURCE: math.ceil(math.log2(len(self.node_vars))),
            ET.TARGET: math.ceil(math.log2(len(self.node_vars))),
        }
        
        if self.max_failovers > 0:
            self.encoding_counts[ET.EDGE] = math.ceil(math.log2(1+len(self.edge_vars)))
            
         
        self.encoded_node_vars :list[str]= []
        self.encoded_source_vars :list[str]= []
        self.encoded_target_vars :list[str]= []
        
        
    def get_index(self, item, type: ET, demand=0):
        if type == ET.NODE:
            return self.node_vars[item]

        if type == ET.EDGE:
            return self.edge_vars[item]

        if type == ET.DEMAND:
            assert isinstance(item, int)
            return item
        
        if type == ET.CHANNEL:
            for i, c in enumerate(self.unique_channels):
                if c == item:
                    return i
                
        if type == ET.PATH:
            for i, p in enumerate(self.paths):
                if p == item:
                    return i

        print(f"We outta here, item did not exist homie: type: {type} item: {item}, here: ")
        traceback.print_stack()
        exit(404)
    
    def make_subst_mapping(self, l1: list[str], l2: list[str]):
        return {l1_e: l2_e for (l1_e, l2_e) in zip(l1, l2)}


    def equals(self, e1: list[str], e2: list[str]):
        assert len(e1) == len(e2)

        expr = self.bdd.true
        for (var1, var2) in zip(e1,e2):
            s = (self.bdd.var(var1) & self.bdd.var(var2)) |(~self.bdd.var(var1) & ~self.bdd.var(var2))
            expr = expr & s

        return expr

    
    def encode(self, type: ET, number: int, demand_number=None):
        encoding_count = self.encoding_counts[type]
        encoding_expr = self.bdd.true
        for j in range(encoding_count):
            post_fix = f"_{demand_number}" if demand_number is not None else ""

            v = self.bdd.var(f"{prefixes[type]}{j+1}"+ post_fix) 
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
        for path in range(1,self.encoding_counts[ET.PATH]+1):
            l1.append(self.get_p_var(path, None, override))
            l2.append(self.get_p_var(path, demand, override))

        return self.make_subst_mapping(l1, l2)
    
    def get_e_var(self, edge: int, failover_edge =  None, override = None):
        if override is None:
            return f"{prefixes[ET.EDGE]}{edge}{f'_{failover_edge}' if failover_edge is not None else ''}"
        
        return f"{override}{edge}{f'_{failover_edge}' if failover_edge is not None else ''}"


    def get_e_vector(self, failover_edge: int , override = None):
        l1 = []
        l2 = []
        for edge in range(1,self.encoding_counts[ET.EDGE]+1):
            l1.append(self.get_e_var(edge, None, override))
            l2.append(self.get_e_var(edge, failover_edge, override))


        return self.make_subst_mapping(l1, l2)

    def get_channel_var(self, channel: int, demand = None, override = None):
        if override is  None:
            return f"{prefixes[ET.CHANNEL]}{channel}{f'_{demand}' if demand is not None else ''}"
        
        return f"{override}{channel}{f'_{demand}' if demand is not None else ''}"
    
    def get_channel_vector(self, demand: int, override = None):
        l1 = []
        l2 = []
        for channel in  range(1,self.encoding_counts[ET.CHANNEL]+1):
            l1.append(self.get_channel_var(channel, None, override))
            l2.append(self.get_channel_var(channel, demand, override))

        return self.make_subst_mapping(l1, l2)
    
    def get_prefix_multiple(self, type: ET, multiple: int):
        return "".join([prefixes[type] for _ in range(multiple)])

    def get_encoding_var_list(self, type: ET, override_prefix = None):
        offset = 0
       
        return [f"{prefixes[type] if override_prefix is None else override_prefix}{i+1 - offset}" for i in range(self.encoding_counts[type])]

    
    def gen_vars(self, ordering: list[ET]):
        for type in ordering:
            if type == ET.DEMAND:
                self.declare_variables(ET.DEMAND)
                self.declare_variables(ET.DEMAND, 2)
            elif type == ET.PATH:
                self.declare_generic_and_specific_variables(ET.PATH, list(range(1, 1 + self.encoding_counts[ET.PATH])))
            elif type == ET.EDGE:
                if self.max_failovers:
                    self.declare_variables(ET.EDGE)
                    self.declare_variables(ET.EDGE, 2)
            elif type in [ET.NODE,ET.SOURCE,ET.TARGET]:
                self.declare_variables(type)
            elif type == ET.CHANNEL:
                self.declare_generic_and_specific_variables(ET.CHANNEL, list(range(1, 1 + self.encoding_counts[ET.CHANNEL])))
            else: 
                raise Exception(f"Error: the given type {type} did not match any BDD type.")

    def declare_variables(self, type: ET, prefix_count: int = 1):
        d_bdd_vars = [f"{self.get_prefix_multiple(type, prefix_count)}{self.encoding_counts[type] - i}" for i in range(0,self.encoding_counts[type])]
        self.bdd.declare(*d_bdd_vars)
        
        return d_bdd_vars

    def declare_generic_and_specific_variables(self, type: ET, l: list[int]):
        bdd_vars = []
        
        for item in l:
            for demand in self.demand_vars.keys():
                bdd_vars.append(f"{prefixes[type]}{item}_{demand}")
                bdd_vars.append(f"{self.get_prefix_multiple(type,2)}{item}_{demand}")
                
        for item in l:
            bdd_vars.append(f"{prefixes[type]}{item}")
            bdd_vars.append(f"{self.get_prefix_multiple(type,2)}{item}")
        
        self.bdd.declare(*bdd_vars)

    def count(self, expr):
        return expr.count(nvars=(((self.encoding_counts[ET.PATH]+self.encoding_counts[ET.CHANNEL]))*(len(self.demand_vars.keys())))+self.encoding_counts[ET.EDGE])

    def count_paths(self, expr):
        c_vars = []
        for demand in self.demand_vars:
            c_vars.extend(self.get_channel_vector(demand).values())
                        
        return expr.exist(*c_vars).count(nvars=(((self.encoding_counts[ET.PATH]))*(len(self.demand_vars.keys()))))

        
    def get_assignments(self, expr,amount, failover):
        
        
        care_vars = []
        
        for d in self.demand_vars:
            care_vars.extend(self.get_channel_vector(d).values())
            care_vars.extend(self.get_p_vector(d).values())
        
        for failover in range(1,self.max_failovers+1):
            for e in range(1, self.encoding_counts[ET.EDGE]+1):
                care_vars.append(f"{prefixes[ET.EDGE]}{e}_{failover}")
        
        
        assignments = []
        
        for a in (self.bdd.pick_iter(expr, care_vars)):
            
            if len(assignments) == amount:
                return assignments
        
            assignments.append(a)
        
        return assignments

    def get_p_assignments(self, expr):
        care_vars = []
        c_vars = []
        for d in self.demand_vars:
            care_vars.extend(self.get_p_vector(d).values())
            c_vars.extend(self.get_channel_vector(d).values())
        
        p_only_expr = self.bdd.exist(c_vars, expr)
        
        return list(self.bdd.pick_iter(p_only_expr, care_vars))
    
    def pretty_print(self, expr, i = 100000, failover=False):
        ass: list[dict[str, bool]] = self.get_assignments(expr, i, failover)
        for a in ass:         
            print(dict(sorted(a.items())))
    
    def query_failover(self, expr, edges: list[tuple[int,int,int]]):
        start = time.perf_counter()
        paths = []

        for path in self.paths:
            for edge in edges:
                if edge in path and path not in paths:
                    paths.append(self.get_index(path, ET.PATH))
        
        failover = self.bdd.true

        for demand in self.demand_vars:
            for path in paths:
                if path in self.d_to_paths[demand]:
                    failover &= ~self.encode(ET.PATH, path, demand)
        
        self.failover_query_time = time.perf_counter() - start
        
        return expr & failover

    def optimize(self):
        _BDD.reorder(self.bdd)
        if not has_cudd:
            self.bdd.collect_garbage()




class DynamicVarsBDD(BaseBDD):
    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand], channel_data: ChannelData, ordering: list[ET], reordering=True, paths=[], overlapping_paths=[], gen_vars=True, failover=0):
        super().__init__(topology, demands, channel_data, ordering, reordering, paths, overlapping_paths, failover)
        
        self.encoding_counts = {
            ET.DEMAND:  math.ceil(math.log2(len(self.demand_vars))),
            ET.CHANNEL:  {d: max(1, math.ceil(math.log2(len(self.channel_data.channels[d])))) for d in self.demand_vars.keys()},
            ET.PATH:  {d: max(1, math.ceil(math.log2(len(self.d_to_paths[d])))) for d in self.demand_vars.keys()}, 
        } 
        
        self.max_failovers = failover

        if self.max_failovers > 0:
            self.encoding_counts[ET.EDGE] = math.ceil(math.log2(1+len(self.edge_vars))) #+1 to for e_unused 

            bdd_vars = []
            for e in range(1,self.encoding_counts[ET.EDGE]+1):
                for failover in range(1,self.max_failovers+1):
                    bdd_vars.append(f"{prefixes[ET.EDGE]}{e}")
                    bdd_vars.append(f"{prefixes[ET.EDGE]}{e}_{failover}")
            self.bdd.declare(*bdd_vars)

        if gen_vars:
            self.gen_vars(ordering)
    
    def count(self, expr):
        nvars = 0

        c_vars = []
        for demand in self.demand_vars:
            c_vars.extend(self.get_channel_vector(demand).values())

        for d in self.demand_vars.keys():
            nvars += self.encoding_counts[ET.PATH][d] #+ self.encoding_counts[ET.CHANNEL][d]
        for i in range(self.max_failovers):
            nvars += self.encoding_counts[ET.EDGE]
        return expr.exist(*c_vars).count(nvars=nvars)

    def gen_vars(self, ordering):
        for type in ordering:
            if type == ET.PATH:
                bdd_vars = []
                for d in self.demand_vars.keys():
                    p_vars = list(range(1, 1 + self.encoding_counts[ET.PATH][d]))
                    
                    for item in p_vars:
                        bdd_vars.append(f"{prefixes[type]}{item}_{d}")
                    
                self.bdd.declare(*bdd_vars)    
            elif type == ET.CHANNEL:
                bdd_vars = []
                for d in self.demand_vars.keys():
                    c_vars = list(range(1, 1 + self.encoding_counts[ET.CHANNEL][d]))
                    
                    for item in c_vars:
                        bdd_vars.append(f"{prefixes[type]}{item}_{d}")
                    
                self.bdd.declare(*bdd_vars)  
            elif type == ET.EDGE:
                if self.max_failovers:
                    self.declare_variables(ET.EDGE)
                # self.declare_variables(ET.EDGE, 2)
            else: 
                pass
                #raise Exception(f"Error: the given type {type} did not match any BDD type.")
    
    def get_index(self, item, type: ET, demand: int):
        if type not in [ET.CHANNEL, ET.PATH]:
            return super().get_index(item, type)
        
        if type == ET.CHANNEL:
            for i, c in enumerate(self.demand_to_channels[demand]):
                if c == item:
                    return i
        
        if type == ET.PATH:
            for i, p in enumerate(self.d_to_paths[demand]):
                if item == p:
                    return i
        
        print(f"We outta here, item did not exist for dynamic vars homie: type: {type} item: {item}, here: ")
        traceback.print_stack()
        exit(404)
    
    def get_global_index(self, item, type: ET):
        return super().get_index(item, type)
        
    def encode(self, type: ET, number: int, demand_number = None):
        encoding_count = self.encoding_counts[type]
        if type == ET.PATH or type == ET.CHANNEL:
            encoding_count = encoding_count[demand_number]
        
        encoding_expr = self.bdd.true
        
        for j in range(encoding_count):
            
            post_fix = f"_{demand_number}" if not demand_number == None else ""
            
            v = self.bdd.var(f"{prefixes[type]}{j+1}" + post_fix) 
            if not (number >> (j)) & 1:
                v = ~v

            encoding_expr = encoding_expr & v
          
        return encoding_expr

    def get_p_vector(self, demand: int , override = None):
        l1 = []
        l2 = []
        for path in range(1,self.encoding_counts[ET.PATH][demand]+1):
            l1.append(self.get_p_var(path, None, override))
            l2.append(self.get_p_var(path, demand, override))

        return self.make_subst_mapping(l1, l2)
    
    def get_channel_vector(self, demand: int, override = None):
        l1 = []
        l2 = []
        for channel in  range(1,self.encoding_counts[ET.CHANNEL][demand]+1):
            l1.append(self.get_channel_var(channel, None, override))
            l2.append(self.get_channel_var(channel, demand, override))

        return self.make_subst_mapping(l1, l2)
    
    def query_failover(self, expr, edges: list[tuple[int,int,int]]):
        start = time.perf_counter()
        failover = self.bdd.true
        
        for demand in self.demand_vars:
            for path_index in self.d_to_paths[demand]:
                path = self.paths[path_index]
                
                for edge in edges:
                    if edge in path:
                        index = self.get_index(path_index, ET.PATH, demand)
                        failover &= ~self.encode(ET.PATH, index, demand)
        
        self.failover_query_time = time.perf_counter() - start
        
        return expr & failover
    
class SubSpectrumDynamicVarsBDD(DynamicVarsBDD):
    def __init__(self, topology, demands, channel_data, ordering, reordering=True, paths=[], overlapping_paths=[], max_demands=128,failovers=0):
        super().__init__(topology,demands, channel_data, ordering, reordering,paths,overlapping_paths, gen_vars=False,failover=failovers)
              
        self.encoding_counts[ET.DEMAND] = max(1, math.ceil(math.log2(max_demands)))
        
        self.gen_vars(ordering)    





      
        
