  
from enum import Enum
import time
import traceback
from rsa_mip import SolveRSAUsingMIP
import os
import json
from fast_rsa_heuristic import fastHeuristic
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
import topology
from topology import d_to_legal_path_dict
import numpy


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
    def __init__(self, demands, slots, use_lim=False, cliques=[], clique_limit=False, sub_spectrum=False, sub_spectrum_k=1):
        self.input = (demands, slots, use_lim, cliques, clique_limit, sub_spectrum, sub_spectrum_k)
        self.channels = topology.get_channels(demands, number_of_slots=slots, limit=use_lim, cliques=cliques, clique_limit=clique_limit)          
        self.splits = [[list(demands.keys())]]

        if sub_spectrum:
            self.splits = [list(a) for a in numpy.array_split(list(demands.keys()), sub_spectrum_k)]
            interval = math.ceil(slots / sub_spectrum_k)
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
                 paths=[],overlapping_paths = [],
                ):
        
        self.bdd = _BDD()
        self.topology = topology
        self.reordering = reordering
        self.ordering = ordering
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

        self.encoding_counts = {
            ET.NODE: math.ceil(math.log2(len(self.node_vars))),
            ET.DEMAND:  math.ceil(math.log2(len(self.demand_vars))),
            ET.CHANNEL:  max(1, math.ceil(math.log2(len(self.unique_channels)))),
            ET.PATH:  max(1, math.ceil(math.log2(len(self.paths)))),
            ET.SOURCE: math.ceil(math.log2(len(self.node_vars))),
            ET.TARGET: math.ceil(math.log2(len(self.node_vars))),
        }
         
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
                pass
                # self.declare_variables(ET.EDGE)
                # self.declare_variables(ET.EDGE, 2)
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
        return expr.count(nvars=(((self.encoding_counts[ET.PATH]+self.encoding_counts[ET.CHANNEL]))*(len(self.demand_vars.keys()))))

    def count_paths(self, expr):
        c_vars = []
        for demand in self.demand_vars:
            c_vars.extend(self.get_channel_vector(demand).values())
                        
        return expr.exist(*c_vars).count(nvars=(((self.encoding_counts[ET.PATH]))*(len(self.demand_vars.keys()))))

        
    def get_assignments(self, expr,amount):
        
        
        care_vars = []
        for d in self.demand_vars:
            care_vars.extend(self.get_channel_vector(d).values())
            care_vars.extend(self.get_p_vector(d).values())
        
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
    
    def pretty_print(self, expr, i = 100000):
        ass: list[dict[str, bool]] = self.get_assignments(expr, i)
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

class DefaultBDD(BaseBDD):
    def __init__(self, topology, demands, channel_data, ordering, reordering=True, paths=[], overlapping_paths=[]):
        super().__init__(topology,demands, channel_data, ordering, reordering,paths,overlapping_paths)
        self.gen_vars(ordering)

class DynamicBDD(BaseBDD):
    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand], channel_data, ordering: list[ET], init_demand=0, max_demands=128, reordering=True):
        super().__init__(topology, demands, channel_data, ordering, reordering)

        self.demand_vars = {(init_demand+i):d for i,d in enumerate(demands.values())}
                
        self.encoding_counts[ET.DEMAND] = max(1, math.ceil(math.log2(max_demands)))

        self.gen_vars(ordering)
    

class SubSpectrumBDD(BaseBDD):
    def __init__(self, topology, demands, channel_data, ordering, reordering=True, paths=[], overlapping_paths=[], max_demands=128):
        super().__init__(topology,demands, channel_data, ordering, reordering,paths,overlapping_paths)
              
        self.encoding_counts[ET.DEMAND] = max(1, math.ceil(math.log2(max_demands)))
        self.encoding_counts[ET.PATH] = max(1, math.ceil(math.log2(len(paths))))
        
        self.gen_vars(ordering)    

class SplitBDD(BaseBDD):
    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand], ordering: list[ET], 
                channel_data:ChannelData, reordering=True, paths=[],overlapping_paths = [], total_number_of_paths= -1):
        
        super().__init__(topology, demands, channel_data, ordering, reordering, paths, overlapping_paths)
        
        self.node_vars = {n: nId[1] for n, nId in zip(topology.nodes, topology.nodes(data=("id")))} 
        self.edge_vars = {e: eId[3] for e, eId in zip(topology.edges(keys=True), topology.edges(keys=True, data=("id")))}
        self.channel_data = channel_data

        self.encoding_counts = {
            ET.NODE: math.ceil(math.log2(1+(max([i for n, i in self.node_vars.items()])))),
            ET.EDGE:  math.ceil(math.log2(1+(max([i for e, i in self.edge_vars.items()])))), 
            ET.DEMAND:  math.ceil(math.log2(max(max(max([i for i, d in self.demand_vars.items()]), len(self.demand_vars)), 2))),
            ET.PATH:   (math.ceil(math.log2(total_number_of_paths))),
            ET.SOURCE: math.ceil(math.log2(1+(max([i for n, i in self.node_vars.items()])))),
            ET.TARGET: math.ceil(math.log2(1+(max([i for n, i in self.node_vars.items()])))),
            ET.CHANNEL:  max(1, math.ceil(math.log2(len(self.unique_channels))))
        }
       
        self.gen_vars(ordering)
    
    def get_encoding_var_list(self, type: ET, override_prefix = None):
        offset = 0
       
        return [f"{prefixes[type] if override_prefix is None else override_prefix}{i+1 - offset}" for i in range(self.encoding_counts[type])]

    

class DynamicVarsBDD(BaseBDD):
    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand], channel_data: ChannelData, ordering: list[ET], reordering=True, paths=[], overlapping_paths=[]):
        super().__init__(topology, demands, channel_data, ordering, reordering, paths, overlapping_paths)
        
        self.encoding_counts = {
            ET.DEMAND:  math.ceil(math.log2(len(self.demand_vars))),
            ET.CHANNEL:  {d: max(1, math.ceil(math.log2(len(self.channel_data.channels[d])))) for d in self.demand_vars.keys()},
            ET.PATH:  {d: max(1, math.ceil(math.log2(len(self.d_to_paths[d])))) for d in self.demand_vars.keys()}, 
        } 
        
        self.gen_vars(ordering)
    
    def count(self, expr):
        nvars = 0

        c_vars = []
        for demand in self.demand_vars:
            c_vars.extend(self.get_channel_vector(demand).values())

        for d in self.demand_vars.keys():
            nvars += self.encoding_counts[ET.PATH][d] #+ self.encoding_counts[ET.CHANNEL][d]

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
            else: 
                pass
                #raise Exception(f"Error: the given type {type} did not match any BDD type.")
    
    def get_index(self, item, type: ET, demand: int):
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

class FixedChannelsBDD(DefaultBDD):
    def save_to_json(self, data, dir,  filename):
        with open(dir + "/" + filename, 'w') as json_file:
            json.dump(data, json_file, indent=4)


    def load_from_json(self, folder, filename):
        filepath = os.path.join(folder, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as json_file:
                data = json.load(json_file)
                return {int(key): value for key, value in data.items()}
        else:
            return None
            
    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand], channel_data: ChannelData, ordering: list[ET], reordering=True,
                 mip_paths=[], bdd_overlapping_paths=[], bdd_paths = [], dir_of_info = "", channel_file_name = "", demand_file_name = "", slots_used = 50, load_cache=True):
        super().__init__(topology, demands, channel_data, ordering, reordering, bdd_paths, bdd_overlapping_paths)
        
        loaded =  self.load_from_json(dir_of_info, channel_file_name)
        if load_cache and loaded is not None:
            print("LOADING CHANNELS FROM PREVIOUS CALCULATIONS!!!! CATUOIUS IS REQUEIRIED")
            self.demand_to_channels = loaded
        else: 
            print("about to start mip :)")
            _,_,_,_,res = SolveRSAUsingMIP(topology, demands, mip_paths, channel_data.unique_channels, slots_used)
            if res is None:
                print("error")
                exit()
            self.demand_to_channels = res
            print("we just solved mip :)")
            if load_cache:
                self.save_to_json(self.demand_to_channels, dir_of_info, str(len(demands)))

        slots_used = []
        
        #! ONLY WORKS FOR ONE CHANNEL PR DEMAND
        for channels in self.demand_to_channels.values():
            slots_used.extend(channels[0])
        
        self.usage = len(set(slots_used))

class FixedChannelsDynamicVarsBDD(DynamicVarsBDD):   
    def save_to_json(self, data, dir, filename):
        if not os.path.exists(dir):
            os.makedirs(dir)

        with open(os.path.join(dir,filename), 'w') as json_file:
            json.dump(data, json_file, indent=4)

    def count(self, expr):
        nvars = 0

        c_vars = []
        for demand in self.demand_vars:
            c_vars.extend(self.get_channel_vector(demand).values())

        for d in list(self.demand_vars.keys()):
            nvars += self.encoding_counts[ET.PATH][d] #+ self.encoding_counts[ET.CHANNEL][d]

        return expr.exist(*c_vars).count(nvars=nvars)


    def load_from_json(self, folder, filename):
        
        filepath = os.path.join(folder, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as json_file:
                data = json.load(json_file)

                return {int(key): value for key, value in data.items()}
        else:
            return None
            
    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand], channel_data: ChannelData, ordering: list[ET], reordering=True,
                 mip_paths=[], bdd_overlapping_paths=[], bdd_paths = [], dir_of_info = "", channel_file_name = "", demand_file_name = "", 
                 slots_used = 50, load_cache=True, use_mip = False):
        super().__init__(topology, demands, channel_data, ordering, reordering, bdd_paths, bdd_overlapping_paths)
        
        loaded =  self.load_from_json(dir_of_info, channel_file_name)
        if load_cache and loaded is not None:
            print("LOADING CHANNELS FROM PREVIOUS CALCULATIONS!!!! CATUOIUS IS REQUEIRIED")
            self.demand_to_channels = loaded
        else: 
            if use_mip: 
                print("about to start mip :)")
                _,_,_,_,res = SolveRSAUsingMIP(topology, demands, mip_paths, channel_data.unique_channels, slots_used)
            else: 
                print("about to start fast")
                res, _ = fastHeuristic(topology, demands, mip_paths, slots_used) 
            if res is None:
                print("error")
                exit()
            self.demand_to_channels = res
            print("we just solved mip :)")
            self.save_to_json(self.demand_to_channels, dir_of_info, str(len(demands)))
        
        slots_used = []
        #! ONLY WORKS FOR ONE CHANNEL PR DEMAND
        for channels in self.demand_to_channels.values():
            slots_used.extend(channels[0])
        
        self.usage = len(set(slots_used))
        
class OnePathBDD(BaseBDD):
    def __init__(self, topology, demands, channel_data, ordering, reordering=True, paths=[], overlapping_paths=[]):
        super().__init__(topology,demands, channel_data, ordering, reordering,paths,overlapping_paths)
        
        self.encoding_counts = {
            ET.CHANNEL: max(1, math.ceil(math.log2(len(self.unique_channels))))
        }

        self.gen_vars(ordering)

    def gen_vars(self,ordering):
        for type in ordering:
            if type == ET.CHANNEL:
                self.declare_generic_and_specific_variables(ET.CHANNEL, list(range(1,1+self.encoding_counts[ET.CHANNEL])))

    def get_assignments(self, expr,amount):
        
        care_vars = []
        for d in self.demand_vars:
            care_vars.extend(self.get_channel_vector(d).values())
        
        assignments = []
        
        for a in (self.bdd.pick_iter(expr, care_vars)):
            
            if len(assignments) == amount:
                return assignments
        
            assignments.append(a)
        
        return assignments