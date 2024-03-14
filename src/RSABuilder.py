from enum import Enum
from typing import Callable
from networkx import MultiDiGraph
from demands import Demand
from niceBDD import *
from niceBDDBlocks import ChannelFullNoClashBlock, ChannelNoClashBlock, ChannelOverlap, ChannelSequentialBlock, DynamicAddBlock, ChangedBlock, DemandPathBlock, EncodedFixedPathBlock, FixedPathBlock, InBlock, ModulationBlock, OutBlock, PathOverlapsBlock, PassesBlock, PathBlock, RoutingAndChannelBlock, SingleOutBlock, SourceBlock, SplitAddAllBlock, SplitAddBlock, TargetBlock, TrivialBlock
from niceBDDBlocks import EncodedFixedPathBlockSplit, EncodedChannelNoClashBlock, PathEdgeOverlapBlock, FailoverBlock, EncodedPathCombinationsTotalyRandom
import topology
import demand_ordering
import rsa.rsa_draw

class AllRightBuilder:
   
    class PathType(Enum):
        DEFAULT=0
        DISJOINT=1
        SHORTEST=2
    
    def set_paths(self, k_paths, path_type):
        self.__paths = self.get_paths(k_paths, path_type)
        self.__overlapping_paths = topology.get_overlapping_simple_paths(self.__paths)
        
        demand_to_paths = {i : [p for j,p in enumerate(self.__paths) if p[0][0] == d.source and p[-1][1] == d.target] for i, d in enumerate(self.__demands.values())}

        for i, d in enumerate(self.__demands.values()):
            d.modulations = [self.__distance_modulation(p) for p in demand_to_paths[i]]

        self.__channel_data = ChannelData(self.__demands, self.__number_of_slots, self.__lim, self.__cliques)
        
    def __init__(self, G: MultiDiGraph, demands: dict[int, Demand], k_paths: int, slots = 320):
        self.__topology = G
        self.__demands = demands
        self.__inc = False 
        
        self.__dynamic = False
        self.__dynamic_max_demands = 128
        
        self.__lim = False
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
    
        self.__cliq = False
        self.__cliques = []
                
        self.__number_of_slots = slots
        self.__channel_data = ChannelData(demands, slots, self.__lim)
        
        self.__modulation = { 0: 3, 250: 4}

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
       
        self.__path_type =  AllRightBuilder.PathType.DEFAULT
        self.__k_paths = k_paths
        self.set_paths(self.__k_paths, self.__path_type)
    
    def count(self):
        return self.result_bdd.base.count(self.result_bdd.expr)
    
    def get_simple_paths(self):
        return self.__paths          

    def get_channels(self):
        return self.__channel_data.channels
    
    def get_unique_channels(self):
        return self.__channel_data.unique_channels
    
    def get_overlapping_channels(self):
        return self.__channel_data.overlapping_channels
    
    def get_demands(self):
        return self.__demands
    
    def get_build_time(self):
        return self.__build_time

    def get_failover_build_time(self):
        return self.__failover_build_time
        
    def dynamic(self, max_demands = 128):
        self.__dynamic = True
        self.__dynamic_max_demands = max_demands
        return self
    
    def failover(self):
        self.__failover = True

        return self

    def path_configurations(self, configurations = 25):
        self.__path_configurations = True
        self.__configurations = configurations
        return self
    
    def limited(self): 
        self.__lim = True
        self.__channel_data = ChannelData(self.__demands, self.__number_of_slots, self.__lim, self.__cliques)

        return self
    
    def sequential(self): 
        self.__lim = True
        self.__seq = True
        self.__channel_data = ChannelData(self.__demands, self.__number_of_slots, self.__lim, self.__cliques)
        
        return self
    
    def clique(self): 
        assert self.__paths != [] # Clique requires some fixed paths to work
        self.__cliq = True
        self.__cliques = topology.get_overlap_cliques(list(self.__demands.values()), self.__paths)
        print("number of channels")
        print(sum([len(self.__channel_data.channels[d]) for d in self.__demands]))
        self.__channel_data = ChannelData(self.__demands, self.__number_of_slots, self.__lim, self.__cliques)
        print("number of channels")
        print(sum([len(self.__channel_data.channels[d]) for d in self.__demands]))
        return self
     
    def get_paths(self, k, path_type: PathType): 
        if path_type == AllRightBuilder.PathType.DEFAULT:
            return topology.get_simple_paths(self.__topology, self.__demands, k)
        elif path_type == AllRightBuilder.PathType.DISJOINT:
            return topology.get_disjoint_simple_paths(self.__topology, self.__demands, k)
        else:
            return topology.get_shortest_simple_paths(self.__topology, self.__demands, k)
    
    def path_type(self, path_type = PathType.DEFAULT):
        self.__path_type = path_type
        self.set_paths(self.__k_paths, self.__path_type)
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
    
    def optimal(self):
        self.__only_optimal = True
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

    def increasing(self):
        self.__inc = True
        return self
    
    
    def modulation(self, modulation: dict[int, int]):
        self.__modulation = modulation
        self.set_paths(self.__k_paths, self.__path_type)
        return self
    
    def __channel_increasing_construct(self):
        assert self.__number_of_slots > 0
        times = []

        lowerBound = 0
        for d in self.__demands.values(): 
            if d.size > lowerBound: 
                lowerBound = d.size

        for slots in range(lowerBound,self.__number_of_slots+1):
            print(slots)
            rs = None
            channel_data = ChannelData(self.__demands, slots, self.__lim)

            if self.__dynamic:
                (rs, build_time) = self.__parallel_construct(channel_data)
            elif self.__split:
                (rs, build_time) = self.__split_construct(channel_data)
            else:
                base = DefaultBDD(self.__topology, self.__demands, channel_data, self.__static_order, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths)
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

        source = SourceBlock(base)
        target = TargetBlock(base)
        
        G = self.__topology if subgraph == None else subgraph
        

        path = base.bdd.true         
        if subgraph is not None:
            path = EncodedFixedPathBlockSplit(self.__graph_to_new_paths[subgraph], base)
        else:
            path = EncodedFixedPathBlock(self.__paths, base)
        pathOverlap = PathOverlapsBlock(base)
    
        modulation = ModulationBlock(base, self.__distance_modulation)
            
        demandPath = DemandPathBlock(path, source, target, base)
        channelOverlap = ChannelOverlap(base)
        
        noClash_expr = EncodedChannelNoClashBlock(pathOverlap, channelOverlap, base)
       
        
        sequential = base.bdd.true
        limitBlock = None
        if self.__seq:
            sequential = ChannelSequentialBlock(base).expr
            print("seqDone")
        if self.__path_configurations:
            limitBlock = EncodedPathCombinationsTotalyRandom(base, self.__configurations)

        rsa = RoutingAndChannelBlock(demandPath, modulation, base, limitBlock, limit=self.__lim)
        fullNoClash = ChannelFullNoClashBlock(rsa.expr & sequential, noClash_expr, base)
        
        return (fullNoClash, time.perf_counter() - start_time)
    

    def __build_failover(self, base):
        startTime = time.perf_counter()
        pathEdgeOverlap = PathEdgeOverlapBlock(base)
        failover = FailoverBlock(base, self.result_bdd, pathEdgeOverlap)
        return (failover, time.perf_counter() - startTime)

    def construct(self):
        assert not (self.__dynamic & self.__seq)
        assert not (self.__split & self.__seq)
        assert not (self.__split & self.__only_optimal)

        base = None


     
        if self.__inc: 
            (self.result_bdd, build_time) = self.__channel_increasing_construct()
        else:
            if self.__dynamic:
                (self.result_bdd, build_time) = self.__parallel_construct()
            elif self.__split:
                (self.result_bdd, build_time) = self.__split_construct()
            else:
                base = DefaultBDD(self.__topology, self.__demands, self.__channel_data, self.__static_order, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths)
                (self.result_bdd, build_time) = self.__build_rsa(base)

        if self.__failover: 
            (self.result_bdd, build_time_failover) = self.__build_failover(base)
            self.__failover_build_time = build_time_failover

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
                assignments = self.result_bdd.base.get_assignments(self.result_bdd.expr, i)
    
            if len(assignments) < i:
                break
    
            rsa.rsa_draw.draw_assignment_path_vars(assignments[i-1], self.result_bdd.base, self.get_simple_paths(), 
                self.get_unique_channels(), self.__topology, file_path, failover=self.__failover)                
         
            if not controllable:
                time.sleep(fps)  
            else:
                input("Proceed?")
            
    
if __name__ == "__main__":
    G = topology.get_nx_graph("topologies/japanese_topologies/dt.gml")
    # G = topology.get_nx_graph("topologies/topzoo/Ai3.gml")
    demands = topology.get_gravity_demands(G, 2,seed=10)
    #demands = demand_ordering.demand_order_sizes(demands)
    print(demands)
    starttime = time.perf_counter()
    p = AllRightBuilder(G, demands, 2).modulation({0:2, 450: 4}).limited().path_type(AllRightBuilder.PathType.DISJOINT).path_configurations(1).construct()
    endtime = time.perf_counter()
    print(endtime-starttime)
    print(p.solved())
    p.draw(10)
    exit()

    print("Don")
    print(p.count())
    #p.result_bdd.base.pretty_print(p.result_bdd.expr)
    
    # exit()
    # p = AllRightBuilder(G, demands).encoded_fixed_paths(3).limited().split(True).construct().draw()
    #baseline = AllRightBuilder(G, demands).encoded_fixed_paths(3).limited().construct()
    
    # print(p.result_bdd.base.bdd == baseline.result_bdd.base.bdd)
    # p.print_result()
    # pretty_print(p.result_bdd.base.bdd, p.result_bdd.expr)
    #print(baseline.size())
    #pretty_print(baseline.result_bdd.base.bdd, baseline.result_bdd.expr)  
    