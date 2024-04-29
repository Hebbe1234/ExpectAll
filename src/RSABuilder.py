from enum import Enum
from typing import Callable
from networkx import MultiDiGraph
from demands import Demand
from niceBDD import *
from niceBDDBlocks import ChannelFullNoClashBlock, ChannelNoClashBlock, ChannelOverlap, ChannelSequentialBlock, DynamicAddBlock, ChangedBlock, DemandPathBlock, DynamicVarsAssignment, DynamicVarsChannelSequentialBlock, DynamicVarsFullNoClash, DynamicVarsNoClashBlock, DynamicVarsRemoveIllegalAssignments, EncodedChannelNoClashBlockGeneric, EncodedFixedPathBlock, FixedPathBlock, InBlock, ModulationBlock, NonChannelOverlap, NonPathOverlapsBlock, OnePathFullNoClashBlock, OutBlock, PathOverlapsBlock, PassesBlock, PathBlock, ReorderedFailoverBlock, RoutingAndChannelBlock, RoutingAndChannelBlockNoSrcTgt, SingleOutBlock, SourceBlock, SplitAddAllBlock, SplitAddBlock, SubSpectrumAddBlock, TargetBlock, TrivialBlock, UsageBlock
from niceBDDBlocks import EncodedFixedPathBlockSplit, EncodedChannelNoClashBlock, PathEdgeOverlapBlock, FailoverBlock, EncodedPathCombinationsTotalyRandom, InfeasibleBlock
from niceBDDBlocks import EdgeFailoverNEvaluationBlock, FailoverBlock2, ReorderedGenericFailoverBlock
 
from japan_mip import SolveJapanMip

import topology
import demand_ordering
import rsa.rsa_draw
from itertools import combinations
from fast_rsa_heuristic import fastHeuristic, calculate_usage
from demand_ordering import demand_order_sizes
from channelGenerator import ChannelGenerator, PathType, BucketType

from demandBuckets import get_buckets_naive,get_buckets_clique, get_buckets_overlapping_graph


from scipy import special as scispec 

class AllRightBuilder:
   
    def set_paths(self, k_paths):
        self.__paths = self.get_paths(k_paths)
        self.__overlapping_paths = topology.get_overlapping_simple_paths(self.__paths)
       
        demand_to_paths = {i : [p for j,p in enumerate(self.__paths) if p[0][0] == d.source and p[-1][1] == d.target] for i, d in enumerate(self.__demands.values())}
 
        for i, d in enumerate(self.__demands.values()):
            d.modulations = list(set([self.__distance_modulation(p) for p in demand_to_paths[i]]))
    
    def set_upper_bound(self):
        _, utilized_dict = fastHeuristic(self.__topology, self.__demands, self.__paths, self.__number_of_slots)
        if utilized_dict is not None:
            self.__number_of_slots = calculate_usage(utilized_dict)
        
        return self
    
    def __init__(self, G: MultiDiGraph, demands: dict[int, Demand], k_paths: int, slots = 320):
        
        self.__topology = G
        self.__demands = demands 
        
        self.__inc = False
        self.__smart_inc = False
        self.__dynamic_vars = False
 
        self.__dynamic = False
        self.__dynamic_max_demands = 128
       
        self.__lim = False
        self.__safe_lim = False
        self.__seq = False
        self.__failover = False
 
        self.__static_order = [ET.EDGE, ET.CHANNEL, ET.NODE, ET.DEMAND, ET.TARGET, ET.PATH, ET.SOURCE]
        self.__reordering = True
 
        self.__path_configurations = False
        self.__configurations = -1
       
        self.__only_optimal = False
       
       
        self.__split = False
        self.__split_add_all = False
        self.__subgraphs = []
        self.__old_demands = demands
        self.__graph_to_new_demands = {}
   
        self.__clique_limit = False
        self.__cliques = []
               
        self.__sub_spectrum = False
        self.__sub_spectrum_max_buckets = 0
        self.__sub_spectrum_buckets = []
        self.__sub_spectrum_usages = []
        self.__sub_spectrum_blocks = []
       
        self.__number_of_slots = slots
        self.__slots_used = slots
        self.__channel_data = None
       
        #self.__modulation = { 0: 3, 250: 4}
        self.__modulation = {0:1}
       
        self.__fixed_channels = False
        self.__fixed_channels_no_join = False
        self.__number_of_bdds = 0
        self.__load_cached_channel_assignments = True
        
        self.result_bdds = []


        self.__onepath = False
        self.__with_evaluation = False
       
        self.__scores = (-1,-1)
        
        self.__output_usage = False
        self.__usage = -1

        self.__use_edge_evaluation = False
        self.__edge_evaluation = {}
        self.__num_of_edge_failures = -1

        self.__use_demand_path = False

        def __distance_modulation(path):
            total_distance = 0
            if type(path) == tuple:
                path = path[1]
           
            for e in path:
                e_data = self.__topology[e[0]][e[1]][e[2]]
                total_distance += e_data["distance"]
               
            crossover_points = list(sorted(self.__modulation.keys()))
            for prev, dist in zip(crossover_points, crossover_points[1:]):
                if total_distance < dist:
                    return self.__modulation[prev]
           
            return self.__modulation[crossover_points[-1]]
       
        self.__distance_modulation = __distance_modulation
       
        self.__k_paths = k_paths
        self.set_paths(self.__k_paths)
   
    def count(self):
        return self.result_bdd.base.count(self.result_bdd.expr)
   
    def get_simple_paths(self):
        return self.__paths          
 
    def get_channels(self):
        return self.__channel_data.channels if self.__channel_data is not None else []
   
    def get_unique_channels(self):
        return self.__channel_data.unique_channels if self.__channel_data is not None else []
   
    def get_overlapping_channels(self):
        return self.__channel_data.overlapping_channels if self.__channel_data is not None else []
   
    def get_demands(self):
        return self.__demands
   
    def get_build_time(self):
        return self.__build_time
 
    def get_failover_build_time(self):
        return self.__failover_build_time
   
    def is_sub_spectrum(self):
        return self.__sub_spectrum
    
    def get_sub_spectrum_blocks(self):
        return self.__sub_spectrum_blocks
   
    # Score is minimal number of needed slots to find one solution (for now anyway)
    def get_optimal_score(self):
        return self.__scores[0]
 
    def get_our_score(self):
        return self.__scores[1]

    
    def count_paths(self):
        return self.result_bdd.base.count_paths(self.result_bdd.expr)
        
    def dynamic(self, max_demands = 128):
        self.__dynamic = True
        self.__dynamic_max_demands = max_demands
        return self
   
    def failover(self,max_failovers=0):
        self.__failover = max_failovers
 
        return self
    
    def use_demand_path(self):
        self.__use_demand_path = True
        return self
 
    def path_configurations(self, configurations = 25):
        self.__path_configurations = True
        self.__configurations = configurations
        return self
   
    def limited(self):
        self.__lim = True
 
        return self
    
    def safe_limited(self):
        self.__safe_lim = True
        return self
   
    def fixed_channels(self, num_of_mip_paths = 2, num_of_bdd_paths = 2, dir_of_channel_assignemnts = "mip_dt", load_cache=True, channel_generator = ChannelGenerator.FASTHEURISTIC, channel_generation = ChannelGeneration.RANDOM, channels_per_demand = 1):
        self.__fixed_channels = True
        self.__num_of_mip_paths = num_of_mip_paths
        self.__num_of_bdd_paths = num_of_bdd_paths
        self.__dir_of_channel_assignments = dir_of_channel_assignemnts
        self.__load_cached_channel_assignments = load_cache
        self.__channel_generator = channel_generator
        self.__channel_generation = channel_generation
        self.__channels_per_demand = channels_per_demand
        self.__dynamic_vars = True

        return self
    
    def no_join_fixed_channels(self, number_of_bdds= -1):
        self.__fixed_channels_no_join = True
        self.__number_of_bdds = number_of_bdds

        return self

    def sequential(self):
        self.__seq = True
       
        return self
   
    def clique(self, clique_limit=False):
        assert self.__paths != [] # Clique requires some fixed paths to work
        self.__clique_limit = clique_limit
        self.__cliques = topology.get_overlap_cliques(list(self.__demands.values()), self.__paths)
           
        return self
     
    def get_paths(self, k):
        return topology.get_disjoint_simple_paths(self.__topology, self.__demands, k)
        
    def no_dynamic_reordering(self):
        self.__reordering = False
        return self
   
    def order(self, new_order):
        assert len(self.__static_order) == len(new_order)
        self.__static_order = new_order
        return self
   
    def reorder_demands(self):
        self.__demands = demand_ordering.demands_reorder_stepwise_similar_first(self.__demands)
        return self
   
    def optimal(self):
        self.__only_optimal = True
        return self
   
    def with_evaluation(self):
        self.__with_evaluation = True
        self.__inc = True
       
        return self
   
    def split(self, add_all = False):
        self.__split = True
        self.__split_add_all = add_all
       
        if self.__topology.nodes.get("\\n") is not None:
            self.__topology.remove_node("\\n")
        for i,n in enumerate(self.__topology.nodes):
            self.__topology.nodes[n]['id'] = i
        for i,e in enumerate(self.__topology.edges):
            self.__topology.edges[e]['id'] = i
       
        self.__subgraphs, removed_node = topology.split_into_multiple_graphs(self.__topology)
        self.__graph_to_new_demands = topology.split_demands2(self.__topology, self.__subgraphs, removed_node, self.__old_demands)
        self.__graph_to_new_paths = topology.split_paths(self.__subgraphs, removed_node, self.__paths)
        self.__graph_to_new_overlap = {}
       
        assert self.__subgraphs is not None # We cannont continue as the graphs was not splittable
           
        for g in self.__subgraphs:
            self.__graph_to_new_overlap[g] = topology.get_overlapping_simple_paths_with_index(self.__graph_to_new_paths[g])
 
        return self
   
    def pruned(self):
        assert self.__paths == [] # Pruning must be done before paths are found
        assert self.__subgraphs == [] # Pruning must be done before the graph is split
 
        self.__topology = topology.reduce_graph_based_on_demands(self.__topology, self.__demands)
        return self
 
    def increasing(self, smart = True):
        self.__inc = True
        self.__smart_inc = smart
        return self
   
    def dynamic_vars(self):
        self.__dynamic_vars = True
        return self
   
    def modulation(self, modulation: dict[int, int]):
        self.__modulation = modulation
        self.set_paths(self.__k_paths)
        return self
   
    def sub_spectrum(self, max_buckets, method=BucketType.NAIVE):
        self.__sub_spectrum = True
        self.__sub_spectrum_max_buckets = max_buckets
        self.__sub_spectrum_type = method
 
        return self
   
    def one_path(self):
        self.__onepath = True
        return self
 
    def output_with_usage(self):
        self.__output_usage = True
        return self

    
    def usage(self):
        return self.__usage
    
    def use_edge_evaluation(self, failurer = 1):
        self.__num_of_edge_failures = failurer
        self.__use_edge_evaluation = True
        return self
    
    def edge_evaluation(self):
        return self.__edge_evaluation
    
    def edge_evaluation_score(self): 
        print("Edge evaluation calculating")
        #doesnt work where out_deg(n1) = in_deg(n2) or vice versa as we will remove trivial cases twice
        def count_trivial_cases():
            count = 0

            for node in self.__topology.nodes():
                out_deg = self.__topology.out_degree(node)
                in_deg = self.__topology.in_degree(node)

                if  out_deg <= self.__num_of_edge_failures:
                    free_edges_in_combination = self.__num_of_edge_failures - out_deg
                    count += scispec.comb(self.__topology.number_of_edges() - out_deg, free_edges_in_combination) #the number of combination of edges (of length num_edge_failure) that contain out_edges of node
                    
                if  in_deg <= self.__num_of_edge_failures:
                    free_edges_in_combination = self.__num_of_edge_failures - in_deg
                    count += scispec.comb(self.__topology.number_of_edges() - in_deg, free_edges_in_combination) #the number of combination of edges (of length num_edge_failure) that contain in_edges of node

            return int(count)
        
        def count_path_trivial_cases():
            def get_combinations(nums, k):
                all_combinations = combinations(nums, k)
                unique_combinations = {tuple(sorted(comb)) for comb in all_combinations}
                return [list(comb) for comb in unique_combinations]

            trivially_false_failure_count = 0
            demand_to_paths = {i : [p for j,p in enumerate(self.__paths) if p[0][0] == d.source and p[-1][1] == d.target] for i, d in enumerate(self.__demands.values())}
            for comb in get_combinations(self.__topology.edges(keys=True), self.__num_of_edge_failures):
                for d in self.__demands:
                    remaining_paths = demand_to_paths[d]
                    for e in comb:
                        remaining_paths = [p for p in remaining_paths if e not in p]

                    if len(remaining_paths) == 0:
                        trivially_false_failure_count += 1
                        break
            
            return trivially_false_failure_count
        
        total_edges = 0
        solved_edges = 0   
        if self.__fixed_channels_no_join :  
            final_edge_evaluation = {e : False for e in set(list(self.no_edge_evaluation[0].keys()))}

            for i,v in final_edge_evaluation.items(): 
                for edge_evaluation in self.no_edge_evaluation:
                    if i not in edge_evaluation: 
                        final_edge_evaluation[i] = True
                        
            for edge_evaluation in self.no_edge_evaluation:
                # print(edge_evaluation)
                for i,v in edge_evaluation.items(): 
                    if v: 
                        final_edge_evaluation[i] = True

            total_edges = len(final_edge_evaluation.keys())
            solved_edges = sum(final_edge_evaluation.values())

        else: 

            for i,v in self.__edge_evaluation.items(): 
                total_edges += 1
                if v: 
                    solved_edges += 1
            
        
        cptc = count_path_trivial_cases()
        return solved_edges, total_edges, (solved_edges * 100)/max(total_edges,1), count_trivial_cases(), cptc, solved_edges + cptc, ((solved_edges + cptc) * 100)/max(total_edges,1)
        
    def __channel_increasing_construct(self):
        def sum_combinations(demands):
            numbers = [m * d.size for d in demands.values() for m in d.modulations ]
            result = set()
            print("initiating smart increasing...")
            for r in range(1,len(numbers)+1):
                for combination in combinations(numbers, r):
                    result.add(sum(combination))
            return sorted(result)
        relevant_slots = []
        if self.__smart_inc :
            relevant_slots = sum_combinations(self.get_demands())
 
        assert self.__number_of_slots > 0
        times = []
 
        lowerBound = 0
       
        if self.__with_evaluation:
            lowerBound = self.__optimal_slots
        else:
            for d in self.__demands.values():
                if min(d.modulations) * d.size > lowerBound:
                    lowerBound = min(d.modulations) * d.size
             
        for slots in range(lowerBound,self.__number_of_slots+1):
            if self.__smart_inc and slots not in relevant_slots:
                continue
           
            print(slots)
            self.__slots_used = slots
            rs = None
           
            channel_data = ChannelData(self.__demands, slots, self.__lim, self.__cliques, self.__clique_limit, self.__sub_spectrum, self.__sub_spectrum_buckets, self.__safe_lim)
 
            if self.__dynamic:
                (rs, build_time) = self.__parallel_construct(channel_data)
            elif self.__split:
                (rs, build_time) = self.__split_construct(channel_data)
            elif self.__sub_spectrum:
                (self.result_bdd, build_time) = self.__sub_spectrum_construct(channel_data)
            else:
                base = None
               
                if self.__dynamic_vars:
                    base = DynamicVarsBDD(self.__topology, self.__demands, channel_data, self.__static_order, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths, failover=self.__failover)
                elif self.__onepath:
                    base = OnePathBDD(self.__topology, self.__demands, channel_data, self.__static_order, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths)
                else:  
                    base = DefaultBDD(self.__topology, self.__demands, channel_data, self.__static_order, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths, failover=self.__failover)
               
                
                (rs, build_time) = self.__build_rsa(base)
 
            times.append(build_time)
 
            assert rs != None
            if not self.__split and rs.expr != rs.expr.bdd.false:
                return (rs, max(times))
            elif self.__split and self.__split_add_all and rs.expr != rs.expr.bdd.false:
                return (rs, max(times))
            elif self.__split and not self.__split_add_all and rs.validSolutions:
                return (rs, max(times))
           
        return (rs, max(times))
     
 
    def __get_buckets(self,type:BucketType, max_k: int):
        if type == BucketType.NAIVE:
            return get_buckets_naive(self.__demands,max_k)
        elif type == BucketType.OVERLAPPING:
            overlapping_graph,certain_overlap = topology.get_overlap_graph(list(self.__demands.values()),self.__paths)
            return get_buckets_overlapping_graph(list(self.__demands.keys()), overlapping_graph, certain_overlap, max_k)

    def __sub_spectrum_construct(self, channel_data=None):
        assert self.__sub_spectrum > 0
        assert self.__channel_data is not None
        
 
        times = []
        rss = []
        for i, s in enumerate(self.__channel_data.splits if channel_data is None else channel_data.splits):
            print(s)
            
            if self.__dynamic_vars:
                base = SubSpectrumDynamicVarsBDD(self.__topology, {k:v for k,v in self.__demands.items() if k in s}, self.__channel_data if channel_data is None else channel_data, self.__static_order, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths, max_demands=len(self.__demands), failover=self.__failover)
            else:
                base = SubSpectrumBDD(self.__topology, {k:v for k,v in self.__demands.items() if k in s}, self.__channel_data if channel_data is None else channel_data, self.__static_order, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths, max_demands=len(self.__demands))
            
            (rs, build_time) = self.__build_rsa(base)
            
            interval = math.ceil(self.__number_of_slots / len(self.__sub_spectrum_buckets))
            self.__sub_spectrum_blocks.append((rs, i*interval, base))
            
            if self.__output_usage:
                self.__sub_spectrum_usages.append(self.__build_sub_spectrum_usage(rs, i * interval))             
            
            print(build_time)
           
            times.append(build_time)
            rss.append(rs)
 
        base = SubSpectrumBDD(self.__topology, self.__demands, self.__channel_data, self.__static_order, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths, max_demands=len(self.__demands))
       
        st = time.perf_counter()
        rs = SubSpectrumAddBlock(rss, base)
        en = time.perf_counter()
       
        return (rs, max(times) + (en-st))
     
 
    def __parallel_construct(self, channel_data = None):
        rsas = []
        rsas_next = []
        n = 1
       
        times = {0:[]}
 
        for i in range(0, len(self.__demands), n):
            base = DynamicBDD(self.__topology, {k:d for k,d in self.__demands.items() if i * n <= k and k < i * n + n }, self.__channel_data if channel_data is None else channel_data ,self.__static_order, init_demand=i*n, max_demands=self.__dynamic_max_demands, reordering=self.__reordering)
            (rsa, build_time) = self.__build_rsa(base)
            rsas.append((rsa, base))
            times[0].append(build_time)
       
        while len(rsas) > 1:
            times[len(times)] = []
 
            rsas_next = []
            for i in range(0, len(rsas), 2):
                if i + 1 >= len(rsas):
                    rsas_next.append(rsas[i])
                    break
               
                start_time = time.perf_counter()
 
                add_block = DynamicAddBlock(rsas[i][0],rsas[i+1][0], rsas[i][1], rsas[i+1][1])
                rsas_next.append((add_block, add_block.base))
 
                times[len(times) - 1].append(time.perf_counter() - start_time)
 
            rsas = rsas_next
       
        full_time = 0
        for k in times:
            full_time += max(times[k])
                   
        return (rsas[0][0], full_time)
   
    def __split_construct(self, channel_data=None):
        assert self.__split and self.__subgraphs is not None
        assert self.__channel_data is not None
        solutions = []
       
        times = []
       
        for g in self.__subgraphs:
            if g in self.__graph_to_new_demands:
                demands = self.__graph_to_new_demands[g]
                paths = self.__graph_to_new_paths[g]
                overlap = self.__graph_to_new_overlap[g]
                base = SplitBDD(g, demands, self.__static_order,  self.__channel_data if channel_data is None else channel_data, self.__reordering, paths, overlap, len(self.__paths))
               
                (rsa1, build_time) = self.__build_rsa(base, g)
                times.append(build_time)
                solutions.append(rsa1)
               
        start_time_add = time.perf_counter()
        if self.__split_add_all:
            return (SplitAddAllBlock(self.__topology, solutions, self.__old_demands, self.__graph_to_new_demands), time.perf_counter() - start_time_add + max(times))
        else:
            return (SplitAddBlock(self.__topology, solutions, self.__old_demands, self.__graph_to_new_demands), time.perf_counter() - start_time_add + max(times))
 
   
    def __build_rsa(self, base, subgraph=None):
        start_time = time.perf_counter()

        if self.__dynamic_vars:                
            seq_expr = base.bdd.true
            
            if self.__seq:
                seq_expr = DynamicVarsChannelSequentialBlock(base).expr

            assignments = DynamicVarsAssignment(seq_expr, self.__distance_modulation, base)
            print("beginning no clash ")
            no_clash = DynamicVarsNoClashBlock(assignments, self.__distance_modulation, base)
            print("done with no clash")

            return (no_clash,  time.perf_counter() - start_time)
           
        if self.__onepath:
            channelOverlap = ChannelOverlap(base)
            return (OnePathFullNoClashBlock(self.__distance_modulation,channelOverlap,base), time.perf_counter() - start_time)
 
 
        source = SourceBlock(base)
        target = TargetBlock(base)
       
        G = self.__topology if subgraph == None else subgraph
       
        path = base.bdd.true        
 
        if subgraph is not None or self.__use_demand_path:
            source = SourceBlock(base)
            target = TargetBlock(base)
            
            if subgraph is not None:
                path = EncodedFixedPathBlockSplit(self.__graph_to_new_paths[subgraph], base)
            else:
                path = EncodedFixedPathBlock(self.__paths, base)
                
            demandPath = DemandPathBlock(path, source, target, base)
       
        modulation = ModulationBlock(base, self.__distance_modulation)
 
        channelOverlap = base.bdd.true
        pathOverlap = base.bdd.true
 
        if len(base.overlapping_channels) < len(base.non_overlapping_channels):
            channelOverlap = ChannelOverlap(base)
        else:
            channelOverlap = NonChannelOverlap(base)
 
       
        if len(base.overlapping_paths) < len(base.non_overlapping_paths):
            pathOverlap = PathOverlapsBlock(base)
        else:
            pathOverlap = NonPathOverlapsBlock(base)
 
 
        noClash_expr = EncodedChannelNoClashBlockGeneric(pathOverlap, channelOverlap, base)
 
 
        sequential = base.bdd.true
        limitBlock = None
 
        if self.__seq:
            sequential = ChannelSequentialBlock(base).expr
            print("seqDone")
        if self.__path_configurations:
            limitBlock = EncodedPathCombinationsTotalyRandom(base, self.__configurations)
        if subgraph is not None or self.__use_demand_path:
            rsa = RoutingAndChannelBlock(demandPath, modulation, base, limitBlock)
 
        else:
            rsa = RoutingAndChannelBlockNoSrcTgt(modulation, base, limitBlock)
 
        fullNoClash = ChannelFullNoClashBlock(rsa.expr & sequential, noClash_expr, base)
       
        return (fullNoClash, time.perf_counter() - start_time)
   
 
    def __build_failover(self, base):
        startTime = time.perf_counter()
        pathEdgeOverlap = PathEdgeOverlapBlock(base)
        failover = FailoverBlock2(base,self.result_bdd,pathEdgeOverlap)
        failover = ReorderedGenericFailoverBlock(base, failover)


        return (failover, time.perf_counter() - startTime)
 
    def __build_usage(self):
        if self.__channel_data is None:
            return -1
        
        if len(self.__sub_spectrum_usages) > 1: 
            return sum(self.__sub_spectrum_usages)
        
        if self.__fixed_channels:
            return self.result_bdd.base.usage
        
        min_usage =  min([len(c) for c in self.__channel_data.unique_channels])
                
        for i in range(min_usage, self.__number_of_slots+1):
            usage_block = UsageBlock(self.result_bdd.base, self.result_bdd, i)
            
            
            if usage_block.expr != self.result_bdd.base.bdd.false:
                return i
            
        
        return self.__number_of_slots
    
    def __build_edge_evaluation(self):
        if self.__fixed_channels_no_join :
            self.no_edge_evaluation = []
            for b in self.result_bdds: 
                b.base.topology = self.__topology
                self.no_edge_evaluation.append(EdgeFailoverNEvaluationBlock(b.base, b, self.__num_of_edge_failures, self.__dynamic_vars).edge_to_failover)
            return None 
        else: 
            k = EdgeFailoverNEvaluationBlock(self.result_bdd.base, self.result_bdd, self.__num_of_edge_failures, self.__dynamic_vars)

        return k.edge_to_failover

    
    def __build_sub_spectrum_usage(self, block, start_index):
        if self.__channel_data is None:
            return -1
        
        min_usage =  min([len(c) for c in self.__channel_data.unique_channels])
        max_slots = math.ceil((self.__number_of_slots) /  len((self.__sub_spectrum_buckets)))
        
        for i in range(min_usage, max_slots + 1):
            usage_block = UsageBlock(block.base, block, i, start_index)
            
            
            if usage_block.expr != block.base.bdd.false:
                return i
            
        return max_slots
    
    def construct(self):
        assert not (self.__dynamic & self.__seq)
        assert not (self.__split & self.__seq)
        assert not (self.__split & self.__only_optimal)

        

        base = None
        if self.__sub_spectrum:
            self.__sub_spectrum_buckets = self.__get_buckets(self.__sub_spectrum_type, self.__sub_spectrum_max_buckets)

        if self.__with_evaluation or self.__only_optimal:
            self.__channel_data = ChannelData(self.__demands, self.__number_of_slots, True, self.__cliques, self.__clique_limit, self.__sub_spectrum, self.__sub_spectrum_buckets)
            print("Running MIP - PLEASE CHECK THAT YOU HAVE INCREASED THE SLURM TIMEOUT TO ALLOW FOR THIS")
            _, _, mip_solves, optimal_slots,_,_ = SolveJapanMip(self.__topology, self.__demands, self.__paths, self.__number_of_slots)
            print("MIP Solved: " + str(mip_solves))
           
            # No reason to keep going if it is not solvable
            if not mip_solves:
                base = DefaultBDD(self.__topology, self.__demands, self.__channel_data, self.__static_order, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths, failover=self.__failover)
                self.result_bdd = InfeasibleBlock(base)
                self.__build_time = 0
                return self
 
            self.__optimal_slots = optimal_slots
            self.__channel_data = ChannelData(self.__demands, optimal_slots, self.__lim, self.__cliques, self.__clique_limit, self.__sub_spectrum, self.__sub_spectrum_buckets, self.__safe_lim)
 
        if self.__channel_data is None:
            self.__channel_data = ChannelData(self.__demands, self.__number_of_slots, self.__lim, self.__cliques, self.__clique_limit, self.__sub_spectrum, self.__sub_spectrum_buckets, self.__safe_lim)
       
        if self.__inc:
            (self.result_bdd, build_time) = self.__channel_increasing_construct()
           
            if self.__with_evaluation:
                self.__scores = (self.__optimal_slots, self.__slots_used)
               
        else:
            if self.__dynamic:
                (self.result_bdd, build_time) = self.__parallel_construct()
            elif self.__split:
                (self.result_bdd, build_time) = self.__split_construct()
            elif self.__sub_spectrum:
                (self.result_bdd, build_time) = self.__sub_spectrum_construct()
            else:
                if self.__fixed_channels:
                    if self.__dynamic_vars:
                        if self.__fixed_channels_no_join:
                            base = NoJoinFixedChannelsBase(self.__topology, self.__demands, self.__channel_data, self.__static_order, reordering=self.__reordering,
                                               num_of_bdd_paths= self.__num_of_bdd_paths, dir_prefix=self.__dir_of_channel_assignments, 
                                               slots_used=self.__slots_used, load_cache=self.__load_cached_channel_assignments, channel_generator = self.__channel_generator,
                                                 channel_generation_teq=self.__channel_generation, paths_for_channel_generator=self.__num_of_mip_paths, channels_per_demand=self.__channels_per_demand, number_of_bdds=self.__number_of_bdds)
                        else:
                            bdd_paths = self.get_paths(self.__num_of_bdd_paths)
                            self.__overlapping_paths = topology.get_overlapping_simple_paths(bdd_paths)
                            base = FixedChannelsDynamicVarsBDD(self.__topology, self.__demands, self.__channel_data, self.__static_order, reordering=self.__reordering,
                                              bdd_overlapping_paths=self.__overlapping_paths, bdd_paths = bdd_paths, dir_prefix=self.__dir_of_channel_assignments, 
                                               slots_used=self.__slots_used, load_cache=self.__load_cached_channel_assignments, channel_generator = self.__channel_generator,
                                                 channel_generation_teq=self.__channel_generation, paths_for_channel_generator=self.__num_of_mip_paths, channels_per_demand=self.__channels_per_demand, failover=self.__failover)
                    # else:
                    #     base = FixedChannelsBDD(self.__topology, self.__demands, self.__channel_data, self.__static_order, reordering=self.__reordering,
                    #                          mip_paths="", bdd_overlapping_paths=self.__overlapping_paths, bdd_paths=bdd_paths,
                    #                            dir_of_info=self.__dir_of_channel_assignments, channel_file_name=str(len(self.__demands)), demand_file_name="", slots_used=self.__slots_used, load_cache=self.__load_cached_channel_assignments)
     
                       
                elif self.__dynamic_vars:
                    base = DynamicVarsBDD(self.__topology, self.__demands, self.__channel_data, self.__static_order, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths, failover=self.__failover)
                elif self.__onepath:
                    base = OnePathBDD(self.__topology, self.__demands, self.__channel_data, self.__static_order, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths)
                else:
                    base = DefaultBDD(self.__topology, self.__demands, self.__channel_data, self.__static_order, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths)
                
                build_time = 0

                if not isinstance(base, NoJoinFixedChannelsBase):
                    (self.result_bdd, build_time) = self.__build_rsa(base)
                else:
                    build_times = []
                    i = 0
                    for base in base.bases:
                        i += 1
                        (result_bdd, build_time) = self.__build_rsa(base)
                        self.result_bdds.append(result_bdd)
                        build_times.append(build_time)

                    build_time = max(build_times)
                    self.result_bdd = self.result_bdds[0]
 
        if self.__failover:
            (self.result_bdd, build_time_failover) = self.__build_failover(base)

            self.__failover_build_time = build_time_failover
 
        if self.__output_usage:
            if isinstance(base, NoJoinFixedChannelsBase) : 
                self.__usage = base.usage
            else:
                self.__usage = self.__build_usage()

        if self.__use_edge_evaluation: 
            self.__edge_evaluation = self.__build_edge_evaluation()

        self.__build_time = build_time
        assert self.result_bdd != None
       
        return self
   

    def solved(self):
        if self.__split and not self.__split_add_all:
            return self.result_bdd.validSolutions
       
        return self.result_bdd.expr != self.result_bdd.base.bdd.false
   
    def size(self):
        if self.__split and not self.__split_add_all:
            return self.result_bdd.get_size()
 
        if not has_cudd:
            self.result_bdd.base.bdd.collect_garbage()
        return len(self.result_bdd.base.bdd)
   
    def print_result(self):
        print("Solvable", "BDD_Size", "Build_Time")
        print(self.solved(), self.size(), self.get_build_time())
 
    def get_assignments(self, amount):
        assignments = []
       
        for a in self.result_bdd.base.bdd.pick_iter(self.result_bdd.expr):
           
            if len(assignments) == amount:
                return assignments
       
            assignments.append(a)
       
        return assignments
   
    def draw(self, amount=1000, fps=1, controllable=True, file_path="./assignedGraphs/assigned"):
        for i in range(1,amount+1):
            assignments = []
            if self.__split and not self.__split_add_all:
                assignments.append(self.result_bdd.get_solution())
            else:
                assignments = self.result_bdd.base.get_assignments(self.result_bdd.expr, i, self.__failover)
   
            if len(assignments) < i:
                break
   
   
            rsa.rsa_draw.draw_assignment_path_vars(assignments[i-1], self.result_bdd.base, self.result_bdd.base.paths,
                self.result_bdd.base.channel_data.unique_channels, self.__topology, file_path, self.__failover)                
         
            if not controllable:
                time.sleep(fps)  
            else:
 
                input("iterate: "+str(i)+ " Proceed?")
                
    def get_the_damn_paths(self):
        return self.__paths
        
        
if __name__ == "__main__":
   # G = topology.get_nx_graph("topologies/topzoo/Ai3.gml")
    G = topology.get_nx_graph("topologies/japanese_topologies/dt.gml")
    # demands = topology.get_demands_size_x(G, 10)
    # demands = demand_ordering.demand_order_sizes(demands)

    num_of_demands = 4
    
    
    # demands = topology.get_gravity_demands_v3(G, num_of_demands, 10, 0, 2, 2, 2)
    demands = topology.get_gravity_demands(G,num_of_demands, multiplier=1)
    #buckets = get_buckets_naive(demands)
 
    print(demands)
    # print(demands)

    # p = AllRightBuilder(G, demands, 2, slots=35).dynamic_vars().use_edge_evaluation(2).construct()
    # print(p.edge_evaluation_score())
    # exit()
    
    p = AllRightBuilder(G, demands, 2, slots=35).dynamic_vars().failover(2).construct()
    
    #p.result_bdd.update_bdd_based_on_edge([9])
    print(p.count())
    p.draw(50000)
    
    exit()
    #p.result_bdd = p.result_bdd.expr
    for seed in range(	15, 16):
        demands = topology.get_gravity_demands(G,num_of_demands, seed=seed, max_uniform=30, multiplier=1)
        print(demands)
        demands = demand_ordering.demand_order_sizes(demands, False)
        print(demands)
        start_time = time.perf_counter()
        p = AllRightBuilder(G, demands, 1, slots=200).dynamic_vars().limited().output_with_usage().construct()
        print(time.perf_counter() - start_time)


#    p = AllRightBuilder(G, demands, 2, slots=320).dynamic_vars().sub_spectrum(5).construct()

    # print(p.get_build_time())
    # print(p.solved())
    #p.result_bdd.expr = p.result_bdd.base.query_failover(p.result_bdd.expr, [(0,3,0), (0,1,0), (5,7,0)])
   # print("query time:", p.result_bdd.base.failover_query_time)
    print("size:", p.size())
    #print(p.usage())

# for seed in range(	15, 16):
#         demands = topology.get_gravity_demands(G,num_of_demands, seed=seed, max_uniform=30, multiplier=1)
#         print(demands)
#         demands = demand_ordering.demand_order_sizes(demands, True)
#         print(demands)
#         start_time = time.perf_counter()
#         p = AllRightBuilder(G, demands, 1, slots=43).dynamic_vars().construct()
#         print(time.perf_counter() - start_time)

#         start_time_constraint, end_time_constraint, solved, optimal, demand_to_channels_res, _ = SolveJapanMip(G, demands, p.get_the_damn_paths(), 100)
        
#         print(solved, p.solved())
#         p.draw(1)
        
#         if optimal != p.usage() and solved:
#             print(f"ERROR: MIP {optimal} vs BDD lim {p.usage()}")
#             print("SEED: ", seed)
#             break
        # print(solved, p.solved())
        # if optimal+1 != p.usage() and solved:
        #     print(f"ERROR: MIP {optimal} vs BDD lim {p.usage()}")
        #     print("SEED: ", seed)
        #     break
    # for seed in range(200, 2000):
    #     demands = topology.get_gravity_demands(G,num_of_demands, seed=seed, max_uniform=30, multiplier=1)
    #     demands = demand_ordering.demand_order_sizes(demands, True)
        
    #     p = AllRightBuilder(G, demands, 1, slots=100).dynamic_vars().limited().output_with_usage().construct()
        
    #     start_time_constraint, end_time_constraint, solved, optimal, demand_to_channels_res, _ = SolveJapanMip(G, demands, p.get_the_damn_paths(), 100)
        
    #     print(solved, p.solved())
    #     if optimal != p.usage() and solved:
    #         print(f"ERROR: MIP {optimal} vs BDD lim {p.usage()}")
    #         print("SEED: ", seed)
    #         break
    
    # exit()

    num_of_demands = 11
    # demands = topology.get_gravity_demands_v3(G, num_of_demands, 10, 0, 2, 2, 2)
    demands = topology.get_gravity_demands(G,num_of_demands, multiplier=1)
    #buckets = get_buckets_naive(demands)
 
    print(demands)
    # print(demands)

    p = AllRightBuilder(G, demands, 2, slots=100).dynamic_vars().set_upper_bound().construct()
    #print(p.edge_evaluation_score())
#    p = AllRightBuilder(G, demands, 2, slots=320).dynamic_vars().sub_spectrum(5).construct()

    print(p.get_build_time())
    # print(p.solved())
    #p.result_bdd.expr = p.result_bdd.base.query_failover(p.result_bdd.expr, [(0,3,0), (0,1,0), (5,7,0)])
   # print("query time:", p.result_bdd.base.failover_query_time)
    print("size:", p.size())
    print(p.usage())
    p.draw(5)
    # Maybe percentages would be better
    # print(p.get_optimal_score())
    # print(p.get_our_score())
    #print(len(p.result_bdd.base.bdd.vars))
    #print("edge Evaluation Dict:", p.edge_evaluation_score())
    #print("count", p.count())
    #print("Don")
    # print("edge Evaluation Dict:", p.edge_evaluation())
    #p.draw(5)
    # exit()



    #p.result_bdd.base.pretty_print(p.result_bdd.expr)
    
    # exit()
    # p = AllRightBuilder(G, demands).encoded_fixed_paths(3).limited().split(True).construct().draw()
    #baseline = AllRightBuilder(G, demands).encoded_fixed_paths(3).limited().construct()
    
    # print(p.result_bdd.base.bdd == baseline.result_bdd.base.bdd)
    # p.print_result()
    # pretty_print(p.result_bdd.base.bdd, p.result_bdd.expr)
    #print(baseline.size())
    #pretty_print(baseline.result_bdd.base.bdd, baseline.result_bdd.expr)  
    



             
# if __name__ == "__main__":
#    # G = topology.get_nx_graph("topologies/topzoo/Ai3.gml")
#     G = topology.get_nx_graph("topologies/japanese_topologies/kanto11.gml")
#     # demands = topology.get_demands_size_x(G, 10)
#     # demands = demand_ordering.demand_order_sizes(demands)
#     num_of_demands = 7
#     # demands = topology.get_gravity_demands_v3(G, num_of_demands, 10, 0, 2, 2, 2)
    
#     demands = topology.get_gravity_demands(G,num_of_demands, max_uniform=10)
#     #demands = demand_ordering.demand_order_sizes(demands)
    

#     print(demands)
#     p = AllRightBuilder(G, demands, 1, slots=25).dynamic_vars().path_type(PathType.DISJOINT).fixed_channels(1,2,"myDirFast", True, False).limited().construct()
#     print(p.get_build_time())
#     print(p.solved())
#     print("size:", p.size())
#     p.draw(5)
