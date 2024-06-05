from networkx import MultiDiGraph
from demands import Demand
from niceBDD import *
from niceBDDBlocks import DynamicVarsAssignment, DynamicVarsChannelSequentialBlock, DynamicVarsNoClashBlock, SlotBindingBlock , SubSpectrumAddBlock, UsageBlock
from niceBDDBlocks import  PathEdgeOverlapBlock 
from niceBDDBlocks import EdgeFailoverNEvaluationBlock, FailoverBlock2, ReorderedGenericFailoverBlock
 
from japan_mip import getLowerBound, getUpperBound

import topology
import demand_ordering
import rsa_draw
from itertools import combinations
from fast_rsa_heuristic import fastHeuristic, calculate_usage
from enums import BucketType

from demandBuckets import get_buckets_naive, get_buckets_overlapping_graph
import random


from scipy import special as scispec 

class ExpectAllBuilder:
   
    def set_paths(self, k_paths):
        self.__paths = topology.get_disjoint_simple_paths(self.__topology, self.__demands, k_paths)

        self.__overlapping_paths = topology.get_overlapping_simple_paths(self.__paths)
       
        demand_to_paths = {i : [p for j,p in enumerate(self.__paths) if p[0][0] == d.source and p[-1][1] == d.target] for i, d in enumerate(self.__demands.values())}
 
        for i, d in enumerate(self.__demands.values()):
            d.modulations = list(set([self.__distance_modulation(p) for p in demand_to_paths[i]]))
    
    def set_heuristic_upper_bound(self):
        _, utilized_dict = fastHeuristic(self.__topology, self.__demands, self.__paths, self.__number_of_slots)
        if utilized_dict is not None:
            self.__number_of_slots = calculate_usage(utilized_dict)
        
        return self
    
    def set_japan_upper_bound(self):
        _, d_to_paths = getLowerBound(self.__topology, self.__demands, self.__paths, self.__number_of_slots)
        print(d_to_paths)
        upperbound = getUpperBound(self.__topology, self.__demands, d_to_paths,self.__paths, self.__number_of_slots)
        self.__number_of_slots = upperbound

        return self
    
    def set_super_safe_upper_bound(self): 
        upper_bound = topology.get_safe_upperbound(self.__demands, self.__paths, self.__number_of_slots)
        self.__number_of_slots = upper_bound + 1
        return self
    
    def __init__(self, G: MultiDiGraph, demands: dict[int, Demand], k_paths: int, slots = 320):
        
        self.__topology = G
        self.__demands = demands 
        
        self.__inc = False
        self.__smart_inc = False
 
        self.__lim = False
        self.__safe_lim = False
        self.__seq = False
        self.__seq_time = 0
        self.__failover = False
 
        self.__static_order = [ET.EDGE, ET.CHANNEL, ET.NODE, ET.DEMAND, ET.TARGET, ET.PATH, ET.SOURCE]
        self.__reordering = True
 
        self.__clique_limit = False
        self.__cliques = []
               
        self.__sub_spectrum = False
        self.__sub_spectrum_max_buckets = 0
        self.__sub_spectrum_buckets = []
        self.__sub_spectrum_usages = []
        self.__sub_spectrum_blocks = []
       
        self.__number_of_slots = slots
        self.__channel_data = None
       
        self.__modulation = {0:1}
       
        self.result_bdds = []

        self.__with_evaluation = False
       
        self.__scores = (-1,-1)
        
        self.__output_usage = False
        self.__usage = -1

        self.__use_edge_evaluation = False
        self.__edge_evaluation = {}
        self.__num_of_edge_failures = -1
        
        self.__no_change_query_times = []
        self.__no_change_query_solved_times = []
        self.__no_change_query_infeasible_counts = []
        self.__no_change_query_solved_counts = []
        self.__no_change_query_not_solved_but_feasible_counts = []
        
        self.__subtree_times = []
        self.__usage_times = []
        self.__time_points = []
        self.__query_times = []
                
        self.__query_impossible_counts = []
                
        self.__with_querying = False
        self.__num_of_queries = 100
        self.__num_of_query_failures = self.__num_of_edge_failures
        self.__query_reaction_time = 0.050


        self.__slot_binding_time = 0
        self.__optimize_time = 0

        self.__failover_build_time = 0
        
        self.__max_required_slot = 0

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
   
   
   
    def optimize(self):
        s = time.perf_counter()
        self.result_bdd.base.optimize()
        self.__optimize_time = time.perf_counter() - s
        return self
   
    def get_optimize_time(self):
        return self.__optimize_time
    
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
        return self.__build_time + self.__slot_binding_time
 
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

    def query_time(self):
        return self.__query_times
    
    def get_time_points(self):
        return self.__time_points
    
    def get_usage_times(self):
        return self.__usage_times
    
    def get_no_change_info(self):
        return self.__no_change_query_times, self.__no_change_query_solved_times, self.__no_change_query_infeasible_counts, self.__no_change_query_solved_counts, self.__no_change_query_not_solved_but_feasible_counts, self.__query_impossible_counts
    
    def count_paths(self):
        return self.result_bdd.base.count_paths(self.result_bdd.expr)
        
   
    def failover(self,max_failovers=0):
        self.__failover = max_failovers
 
        return self
       
    def limited(self):
        self.__lim = True
 
        return self
    
    def safe_limited(self):
        self.__safe_lim = True
        return self
   
    def sequential(self):
        self.__seq = True       
        return self
       
    def get_sequential_time(self):
        return self.__seq_time
   
    def clique(self, clique_limit=False):
        assert self.__paths != [] # Clique requires some fixed paths to work
        self.__clique_limit = clique_limit
        self.__cliques = topology.get_overlap_cliques(self.__demands, self.__paths)
           
        return self
     
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
   
      
    def has_edge_evaluation(self):
       return self.__num_of_edge_failures > 0
   
 
    def increasing(self, smart = True):
        self.__inc = True
        self.__smart_inc = smart
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
   
 
    def output_with_usage(self):
        self.__output_usage = True
        return self

    def usage(self):
        return self.__usage
    
    def use_edge_evaluation(self, failurer = 1):
        self.__num_of_edge_failures = failurer
        self.__use_edge_evaluation = True
        return self
    
    def with_querying(self, failures:int, k=100, reaction_time=0.050):
        for _ in range(failures):
            self.__no_change_query_times.append([])
            self.__no_change_query_solved_times.append([])
            self.__no_change_query_infeasible_counts.append([])
            self.__no_change_query_solved_counts.append([])
            self.__no_change_query_not_solved_but_feasible_counts.append([])
            
            self.__subtree_times.append([])
            self.__usage_times.append([])
            self.__time_points.append([])
            self.__query_times.append([])
            self.__time_points.append([])
            
            self.__query_impossible_counts.append([])

        self.__query_reaction_time = reaction_time
        self.__with_querying = True
        self.__num_of_queries = k
        self.__num_of_query_failures = failures
        return self
    
    def get_subtree_query_times(self):
        return self.__subtree_times
    
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
        

        for i,v in self.__edge_evaluation.items(): 
            total_edges += 1
            if v: 
                solved_edges += 1
            
        
        cptc = count_path_trivial_cases()
        return solved_edges, total_edges, (solved_edges * 100)/max(total_edges,1), count_trivial_cases(), cptc, solved_edges + cptc, ((solved_edges + cptc) * 100)/max(total_edges,1)
            
    def get_max_required_slot(self):
        return self.__max_required_slot
    
    def measure_max_required_slot(self):    
        
        if not self.__with_querying:
            sb_s = time.perf_counter()
            expr_s = SlotBindingBlock(self.result_bdd.base, self.result_bdd.expr).expr
            self.__slot_binding_time = time.perf_counter() -sb_s
            self.result_bdd.expr = expr_s

        i_vars = []
        for i in range(1,self.__failover+1):
            i_vars.extend(self.result_bdd.base.get_e_vector(i).values())
            
            
        c_vars = [f"s_{f}" for f in range(self.__number_of_slots)]
        for d in self.result_bdd.base.demand_vars:
            c_vars.extend(self.result_bdd.base.get_p_vector(d).values())
            c_vars.extend(self.result_bdd.base.get_channel_vector(d).values())

        old = math.inf
        for s in range(self.__number_of_slots, 0, -1):
            expr = self.result_bdd.base.bdd.let({f"s_{s-1}": False}, self.result_bdd.expr)
            expr = expr.exist(*c_vars)
            
            count = expr.count(nvars=len(i_vars))
            if old == math.inf:
                old = count
            elif old > count:
                self.__max_required_slot = s  
                return self
        
        return self
        
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
       

        for d in self.__demands.values():
            if min(d.modulations) * d.size > lowerBound:
                lowerBound = min(d.modulations) * d.size
            
        for slots in range(lowerBound,self.__number_of_slots+1):
            if self.__smart_inc and slots not in relevant_slots:
                continue
           
            print(slots)
            rs = None
           
            channel_data = ChannelData(self.__demands, slots, self.__lim, self.__cliques, self.__clique_limit, self.__sub_spectrum, self.__sub_spectrum_buckets, self.__safe_lim)
 
            if self.__sub_spectrum:
                (self.result_bdd, build_time) = self.__sub_spectrum_construct(channel_data)
            else:
                base = DynamicVarsBDD(self.__topology, self.__demands, channel_data, self.__static_order, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths, failover=self.__failover)
               
                (rs, build_time) = self.__build_rsa(base)
 
            times.append(build_time)
 
            assert rs != None
            if rs.expr != rs.expr.bdd.false:
                return (rs, max(times))
           
        return (rs, max(times))
     
 
    def __get_buckets(self,type:BucketType, max_k: int):
        if type == BucketType.NAIVE:
            return get_buckets_naive(self.__demands,max_k)
        elif type == BucketType.OVERLAPPING:
            overlapping_graph,certain_overlap = topology.get_overlap_graph(self.__demands,self.__paths)
            return get_buckets_overlapping_graph(list(self.__demands.keys()), overlapping_graph, certain_overlap, max_k)

    def __sub_spectrum_construct(self, channel_data=None):
        assert self.__sub_spectrum > 0
        assert self.__channel_data is not None
        
 
        times = []
        rss = []
        for i, s in enumerate(self.__channel_data.splits if channel_data is None else channel_data.splits):
            
            base = SubSpectrumDynamicVarsBDD(self.__topology, {k:v for k,v in self.__demands.items() if k in s}, self.__channel_data if channel_data is None else channel_data, self.__static_order, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths, max_demands=len(self.__demands), failovers=self.__failover)
            
            (rs, build_time) = self.__build_rsa(base)
            
            interval = math.ceil(self.__number_of_slots / len(self.__sub_spectrum_buckets))
            self.__sub_spectrum_blocks.append((rs, i*interval, base))
            
            if self.__output_usage:
                self.__sub_spectrum_usages.append(self.__build_sub_spectrum_usage(rs, i * interval))             
            
            print(build_time)
           
            times.append(build_time)
            rss.append(rs)

        base = SubSpectrumDynamicVarsBDD(self.__topology, self.__demands, self.__channel_data, self.__static_order, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths, max_demands=len(self.__demands))
       
        st = time.perf_counter()
        rs = SubSpectrumAddBlock(rss, base)
        en = time.perf_counter()
       
        return (rs, max(times) + (en-st))
     
   
    def __build_rsa(self, base):
        start_time = time.perf_counter()

        seq_expr = base.bdd.true
        
        if self.__seq:
            s = time.perf_counter()
            seq_expr = DynamicVarsChannelSequentialBlock(base).expr
            self.__seq_time = (time.perf_counter() - s)

        assignments = DynamicVarsAssignment(seq_expr, self.__distance_modulation, base)
        print("beginning no clash ")
        no_clash = DynamicVarsNoClashBlock(assignments, self.__distance_modulation, base)
        print("done with no clash")

        return (no_clash,  time.perf_counter() - start_time)
           

 
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
        
        min_usage =  min([len(c) for c in self.__channel_data.unique_channels])
                
        for i in range(min_usage, self.__number_of_slots+1):
            usage_block = UsageBlock(self.result_bdd.base, self.result_bdd, i)
            
            if usage_block.expr != self.result_bdd.base.bdd.false:
                return i
            
        
        return self.__number_of_slots
    
    def __build_edge_evaluation(self):
        k = EdgeFailoverNEvaluationBlock(self.result_bdd.base, self.result_bdd, self.__num_of_edge_failures, True)

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
    
    
    
    def __measure_query_time_least_path_changes(self, assignment: dict[str, bool],normal_usage, combination: list[tuple[int,int,int]], expr_s):
        
        def power(var: str, type: ET):
            val = int(var.replace(prefixes[type], ""))
            # Total binary vars - var val (hence l1 => |binary vars|)
            exponent = val - 1 
        
            return 2 ** (exponent)
             
        expr = expr_s
        base = self.result_bdd.base
        banned_paths = [p for p in base.paths for e in combination if e in p]

        chosen_paths = {str(d): 0 for d  in base.demand_vars.keys()}
        chosen_channel = {str(d): 0 for d  in base.demand_vars.keys()}

        for k, v in assignment.items():
            if k[0] == prefixes[ET.PATH] and v:
                [p_var, demand_id] = k.split("_")
                chosen_paths[demand_id] += power(p_var, ET.PATH)
            
            if k[0] == prefixes[ET.CHANNEL] and v:
                [c_var, demand_id] = k.split("_")
                chosen_channel[demand_id] += power(c_var, ET.CHANNEL)
                
        for d,p in chosen_paths.items():
            d = int(d)
            concrete_path = base.paths[base.d_to_paths[d][p]]
            if concrete_path in banned_paths:
                d_feasible = False

                for bp in base.d_to_paths[d]:
                    d_feasible |= (base.paths[bp] not in banned_paths)
                
                if not d_feasible:
                    return False, 0, 0, 0, False               
            
        time_start = time.perf_counter()

        
        # prune solutions with these paths and keep old pathjs
        if isinstance(self.result_bdd, ReorderedGenericFailoverBlock):
            expr = self.result_bdd.update_bdd_based_on_edge([self.result_bdd.base.get_index(e, ET.EDGE, 0) for e in combination], expr_s)
            
            for d, p in chosen_paths.items():
                if base.paths[base.d_to_paths[int(d)][p]] not in banned_paths:
                    expr = expr & base.encode(ET.PATH,chosen_paths[str(d)],int(d)) & base.encode(ET.CHANNEL,chosen_channel[str(d)],int(d))
        else:
            demands_using_banned_path = set()

            for d,p in chosen_paths.items():
                d = int(d)
                concrete_path = base.paths[base.d_to_paths[d][p]]
                if concrete_path in banned_paths:
                    demands_using_banned_path.add(d)
                else:
                    expr = expr & base.encode(ET.PATH,chosen_paths[str(d)],d) & base.encode(ET.CHANNEL,chosen_channel[str(d)],int(d))


            for d in demands_using_banned_path:
                for p in base.d_to_paths[d]:
                    concrete_path = base.paths[p]
                    if concrete_path in banned_paths:
                        expr = expr & ~base.encode(ET.PATH,p,d)
            
        time_usage_start = time.perf_counter()    
        if expr != base.bdd.false: 
            for check_slot in range(normal_usage-1 ,self.__number_of_slots):
                result = self.result_bdd.base.bdd.let({f"s_{check_slot}": False}, expr)

                if result != self.result_bdd.base.bdd.false:
                    return True, time.perf_counter() - time_start, time.perf_counter()-time_usage_start,0, True

            return False, time.perf_counter() - time_start, time.perf_counter()-time_usage_start,0, True                
        else:
            return False, time.perf_counter() - time_start, time.perf_counter()-time_usage_start,0,True

    def __measure_query_time(self, num_queries=100, max_reaction_time = 0.050, num_of_edge_failures=0, expr_s=None):
        if expr_s == None:
            expr_s = self.result_bdd.expr
            
        all_combinations = combinations(self.__topology.edges(keys=True), max(num_of_edge_failures,0))
        unique_combinations = {tuple(sorted(comb)) for comb in all_combinations}
        combs = [list(comb) for comb in unique_combinations]
        
        assert self.__channel_data is not None
        min_usage =  min([len(c) for c in self.__channel_data.unique_channels])
        
        no_solutions = True
        query_time = 0
        normal_usage = 0
        all_times = []
        usage_times = []
        subtree_times = []

        no_change_query_times = []
        no_change_query_solved_times = []
        no_change_query_solved_count = 0
        no_change_query_not_solved_but_feasible_count = 0
        no_change_query_infeasible_count = 0
        
        query_impossible_count = 0
        
        for i in range(min_usage, self.__number_of_slots+1):
            usage_block = UsageBlock(self.result_bdd.base, self.result_bdd, i)
            
            if usage_block.expr != self.result_bdd.base.bdd.false:
                normal_usage = i
                no_solutions = False
                break
            
        if no_solutions:
            return 0, all_times, usage_times, subtree_times, no_change_query_times, no_change_query_solved_times, no_change_query_solved_count, no_change_query_not_solved_but_feasible_count, no_change_query_infeasible_count, query_impossible_count
        
        for _ in range(num_queries):
            combination = random.choice(combs)
            optimal_solution = next(usage_block.base.bdd.pick_iter(usage_block.expr))
                
            success, least_change_time, _, _, feasible = self.__measure_query_time_least_path_changes(optimal_solution,normal_usage,combination, expr_s)

            if feasible:
                no_change_query_times.append(least_change_time)
                if success:
                    no_change_query_solved_times.append(least_change_time)
                                              
                no_change_query_solved_count += 1 if success else 0
                no_change_query_not_solved_but_feasible_count += 0 if success else 1
            else:
                no_change_query_infeasible_count += 1
          

            s = time.perf_counter()

            if isinstance(self.result_bdd, ReorderedGenericFailoverBlock):
                failed_expr = self.result_bdd.update_bdd_based_on_edge([self.result_bdd.base.get_index(e, ET.EDGE, 0) for e in combination],expr_s)
            else:
                failed_expr = self.result_bdd.base.query_failover(expr_s, combination)

            all_time_usage_start = time.perf_counter()

            if failed_expr != self.result_bdd.base.bdd.false:
                for check_slot in range(normal_usage-1 ,self.__number_of_slots):
                    result = self.result_bdd.base.bdd.let({f"s_{check_slot}": False}, failed_expr)

                    if result != self.result_bdd.base.bdd.false:
                        break
            else: 
                query_impossible_count += 1
                
            time_end = time.perf_counter()
            
            the_time = (time_end- s)
            query_time += the_time
            
            subtree_time = all_time_usage_start - s
            subtree_times.append(subtree_time)         
                           
            usage_times.append(time_end-all_time_usage_start)
                
            all_times.append(the_time)
            
            
        print(f"Query time: {query_time/num_queries}s == {(query_time*1000)/num_queries}ms")
        return (query_time*1000)/num_queries, all_times, usage_times, subtree_times, no_change_query_times, no_change_query_solved_times, no_change_query_solved_count, no_change_query_not_solved_but_feasible_count, no_change_query_infeasible_count, query_impossible_count
        
        
    
    def construct(self):
        base = None
        build_time = 0

        if self.__sub_spectrum:
            self.__sub_spectrum_buckets = self.__get_buckets(self.__sub_spectrum_type, self.__sub_spectrum_max_buckets)

        
        if self.__channel_data is None:
            self.__channel_data = ChannelData(self.__demands, self.__number_of_slots, self.__lim, self.__cliques, self.__clique_limit, self.__sub_spectrum, self.__sub_spectrum_buckets, self.__safe_lim)
       
        if self.__inc:
            (self.result_bdd, build_time) = self.__channel_increasing_construct()
               
        else:
            if self.__sub_spectrum:
                (self.result_bdd, build_time) = self.__sub_spectrum_construct()

            else:
                base = DynamicVarsBDD(self.__topology, self.__demands, self.__channel_data, self.__static_order, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths, failover=self.__failover)
            

                (self.result_bdd, build_time) = self.__build_rsa(base)
 
        if self.__failover:
            (self.result_bdd, build_time_failover) = self.__build_failover(base)

            self.__failover_build_time = build_time_failover
 
        if self.__output_usage:
            self.__usage = self.__build_usage()

        if self.__use_edge_evaluation: 
            self.__edge_evaluation = self.__build_edge_evaluation()
            
        if self.__with_querying:
            print("Slot binding")
            sb_s = time.perf_counter()
            expr_s = SlotBindingBlock(self.result_bdd.base, self.result_bdd.expr).expr
            self.__slot_binding_time = time.perf_counter() -sb_s
            self.result_bdd.expr = expr_s

            
            for i in range(self.__num_of_query_failures):
                query_time, time_points, usage_times, subtree_times, no_change_query_times, no_change_query_solved_times, no_change_query_solved_count, no_change_query_not_solved_but_feasible_count, no_change_query_infeasible_count, query_impossible_count = self.__measure_query_time(num_queries = self.__num_of_queries,num_of_edge_failures = i+1, expr_s=expr_s , max_reaction_time=self.__query_reaction_time)
                self.__time_points[i] = time_points
                self.__usage_times[i] = usage_times
                self.__subtree_times[i] = subtree_times
                self.__query_times[i] = query_time
                self.__no_change_query_times[i] = no_change_query_times
                self.__no_change_query_solved_times[i] = no_change_query_solved_times
                self.__no_change_query_solved_counts[i] = no_change_query_solved_count
                self.__no_change_query_not_solved_but_feasible_counts[i] = no_change_query_not_solved_but_feasible_count
                self.__no_change_query_infeasible_counts[i] = no_change_query_infeasible_count
                self.__query_impossible_counts[i] = query_impossible_count

        self.__build_time = build_time
        
        assert self.result_bdd != None
       
        return self
   
   

    def solved(self):
        return self.result_bdd.expr != self.result_bdd.base.bdd.false
   
    def size(self): 
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
            assignments = self.result_bdd.base.get_assignments(self.result_bdd.expr, i, self.__failover)
   
            if len(assignments) < i:
                break
   
            rsa_draw.draw_assignment_path_vars(assignments[i-1], self.result_bdd.base, self.result_bdd.base.paths,
                self.result_bdd.base.channel_data.unique_channels, self.__topology, file_path, self.__failover)                
         
            if not controllable:
                time.sleep(fps)  
            else:
 
                input("iterate: "+str(i)+ " Proceed?")
                
    def get_paths(self):
        return self.__paths
    
    def get_slots(self):
        return self.__number_of_slots
        
        
if __name__ == "__main__":
    G = topology.get_nx_graph("topologies/japanese_topologies/kanto11.gml")

    num_of_demands = 3
        
    demands = topology.get_gravity_demands(G,num_of_demands, multiplier=1, max_uniform=30, seed=10)
    demands = demand_ordering.demand_order_sizes(demands)

    print(demands)
    print(sum([d.size for d in demands.values()]))

    p = ExpectAllBuilder(G, demands, 3, slots=100).set_super_safe_upper_bound().failover(2).sequential().safe_limited().construct().measure_max_required_slot()
        
    print("max required:", p.get_max_required_slot())
            