from enum import Enum
from networkx import MultiDiGraph
from demands import Demand
from niceBDD import *
from niceBDDBlocks import ChannelFullNoClashBlock, ChannelNoClashBlock, ChannelOverlap, ChannelSequentialBlock, DynamicAddBlock, ChangedBlock, DemandPathBlock, EncodedFixedPathBlock, FixedPathBlock, InBlock, OutBlock, PathOverlapsBlock, PassesBlock, PathBlock, RoutingAndChannelBlock, SingleOutBlock, SourceBlock, SplitAddAllBlock, SplitAddBlock, TargetBlock, TrivialBlock
from niceBDDBlocks import EncodedFixedPathBlockSplit, EncodedChannelNoClashBlock, PathEdgeOverlapBlock, FailoverBlock
import topology
import rsa.rsa_draw

class AllRightBuilder:
    
    class FixedPathType(Enum):
        DEFAULT=0
        NAIVE=1
        ENCODED=2
    
    class PathType(Enum):
        DEFAULT=0
        DISJOINT=1
        SHORTEST=2
    
    def __init__(self, G: MultiDiGraph, demands: dict[int, Demand], slots = 64):
        self.__topology = G
        self.__demands = demands
        self.__inc = False 
        
        self.__dynamic = False
        self.__dynamic_max_demands = 128
        
        self.__lim = False
        self.__seq = False
        self.__cliq = False 
        self.__failover = False

        self.__static_order = [ET.EDGE, ET.CHANNEL, ET.NODE, ET.DEMAND, ET.TARGET, ET.PATH, ET.SOURCE]
        self.__reordering = True

        self.__pathing = AllRightBuilder.FixedPathType.DEFAULT
        self.__paths = []
        self.__overlapping_paths = []
        
        self.__only_optimal = False
        
        self.__split = False
        self.__split_add_all = False
        self.__subgraphs = []
        self.__old_demands = demands
        self.__graph_to_new_demands = {}
    
        self.__cliques = []
                
        self.__number_of_slots = slots
        self.__channel_data = ChannelData(demands, slots, self.__lim)
        
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
    def limited(self): 
        self.__lim = True
        self.__channel_data = ChannelData(self.__demands, self.__number_of_slots, self.__lim)

        return self
    
    def sequential(self): 
        self.__lim = True
        self.__seq = True
        self.__channel_data = ChannelData(self.__demands, self.__number_of_slots, self.__lim)
        
        return self
    
    def clique(self): 
        assert self.__paths != [] # Clique requires some fixed paths to work
        self.__cliq = True
        self.__cliques = topology.get_overlap_cliques(list(self.__demands.values()), self.__paths)
        return self
    
    def get_paths(self, k, path_type: PathType):
        if path_type == AllRightBuilder.PathType.DEFAULT:
            return topology.get_simple_paths(self.__topology, self.__demands, k)
        elif path_type == AllRightBuilder.PathType.DISJOINT:
            return topology.get_disjoint_simple_paths(self.__topology, self.__demands, k)
        else:
            return topology.get_shortest_simple_paths(self.__topology, self.__demands, k)
    
    def naive_fixed_paths(self, k, path_type = PathType.DEFAULT):
        self.__pathing = AllRightBuilder.FixedPathType.NAIVE
        self.__paths = self.get_paths(k, path_type)
        return self
    
    def encoded_fixed_paths(self, k, path_type = PathType.DEFAULT):
        self.__pathing = AllRightBuilder.FixedPathType.ENCODED
        self.__paths = self.get_paths(k, path_type)
        self.__overlapping_paths = topology.get_overlapping_simple_paths(self.__paths)
        return self
    
    def no_dynamic_reordering(self):
        self.__reordering = False
        return self
    
    def order(self, new_order):
        assert len(self.__static_order) == len(new_order)
        self.__static_order = new_order
        return self
    
    def reorder_demands(self):
        self.__demands = topology.demands_reorder_stepwise_similar_first(self.__topology, self.__demands)
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
                if not self.__dynamic and (self.__pathing == AllRightBuilder.FixedPathType.DEFAULT or self.__pathing == AllRightBuilder.FixedPathType.NAIVE):
                    base = DefaultBDD(self.__topology, self.__demands, channel_data, self.__static_order, reordering=self.__reordering)
        
                elif not self.__dynamic and self.__pathing == AllRightBuilder.FixedPathType.ENCODED:
                    base = DefaultBDD(self.__topology, self.__demands, channel_data, self.__static_order, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths,encoded_paths=True)
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
                base = -1
                if self.__pathing == AllRightBuilder.FixedPathType.ENCODED:
                    paths = self.__graph_to_new_paths[g]
                    overlap = self.__graph_to_new_overlap[g]
                    base = SplitBDD(g, demands, self.__static_order,  self.__channel_data if channel_data is None else channel_data, self.__reordering, paths, overlap, True, len(self.__paths))
                else:
                    base = SplitBDD(g, demands, self.__static_order,  self.__channel_data if channel_data is None else channel_data, reordering=self.__reordering)
                (rsa1, build_time) = self.__build_rsa(base, g)
                times.append(build_time)
                solutions.append(rsa1)
                
        start_time_add = time.perf_counter() 
        if self.__split_add_all:
            return (SplitAddAllBlock(self.__topology, solutions, self.__old_demands, self.__graph_to_new_demands, self.__paths, None, encoded_path=True), time.perf_counter() - start_time_add + max(times))
        else:
            return (SplitAddBlock(self.__topology, solutions, self.__old_demands, self.__graph_to_new_demands, self.__paths, True), time.perf_counter() - start_time_add + max(times))
    
    def __build_rsa(self, base, subgraph=None):
        
        start_time = time.perf_counter()

        source = SourceBlock(base)
        target = TargetBlock(base)
        
        G = self.__topology if subgraph == None else subgraph
        

        path = base.bdd.true 
        pathOverlap = base.bdd.true
        if self.__pathing == AllRightBuilder.FixedPathType.DEFAULT:
            passes = PassesBlock(G, base)

            in_expr = InBlock(G, base)
            out_expr = OutBlock(G, base)
            
            trivial_expr = TrivialBlock(G, base)
            singleOut = SingleOutBlock(out_expr, passes, base)
            changed = ChangedBlock(passes, base)

            path = PathBlock(trivial_expr, out_expr,in_expr, changed, singleOut, base)
        elif self.__pathing == AllRightBuilder.FixedPathType.NAIVE:
            passes = PassesBlock(G, base)
            path = FixedPathBlock(self.__paths, base)
        elif self.__pathing == AllRightBuilder.FixedPathType.ENCODED:
            if subgraph is not None:
                path = EncodedFixedPathBlockSplit(self.__graph_to_new_paths[subgraph], base)
            else:
                path = EncodedFixedPathBlock(self.__paths, base)
            pathOverlap = PathOverlapsBlock(base)
            
        demandPath = DemandPathBlock(path, source, target, base)
        channelOverlap = ChannelOverlap(base)
        
        noClash_expr = base.bdd.true
        if self.__pathing == AllRightBuilder.FixedPathType.ENCODED:
            noClash_expr = EncodedChannelNoClashBlock(pathOverlap, channelOverlap, base)
        else:
            noClash_expr = ChannelNoClashBlock(passes, channelOverlap, base)
        
        sequential = base.bdd.true
        if self.__seq:
            sequential = ChannelSequentialBlock(base).expr
        
        rsa = RoutingAndChannelBlock(demandPath, base, limit=self.__lim)
        fullNoClash = ChannelFullNoClashBlock(rsa.expr & sequential, noClash_expr, base)
        
        return (fullNoClash, time.perf_counter() - start_time)
    

    def __build_failover(self, base):
        startTime = time.perf_counter()
        pathEdgeOverlap = PathEdgeOverlapBlock(base)
        failover = FailoverBlock(base, self.result_bdd, pathEdgeOverlap)
        return (failover, time.perf_counter() - startTime)

    def construct(self):
        assert not (self.__dynamic & (self.__pathing != AllRightBuilder.FixedPathType.DEFAULT))
        assert not (self.__cliq & (self.__pathing == AllRightBuilder.FixedPathType.DEFAULT))
        assert not (self.__dynamic & self.__seq)
        assert not (self.__split & self.__seq)
        assert not (self.__split & self.__only_optimal)

        base = None
        if not self.__dynamic and (self.__pathing == AllRightBuilder.FixedPathType.DEFAULT or self.__pathing == AllRightBuilder.FixedPathType.NAIVE):
            base = DefaultBDD(self.__topology, self.__demands, self.__channel_data, self.__static_order, reordering=self.__reordering)
        
        elif not self.__dynamic and self.__pathing == AllRightBuilder.FixedPathType.ENCODED:
            base = DefaultBDD(self.__topology, self.__demands, self.__channel_data, self.__static_order, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths,encoded_paths=True)
    
        
        if self.__inc: 
            (self.result_bdd, build_time) = self.__channel_increasing_construct()
        else:
            if self.__dynamic:
                (self.result_bdd, build_time) = self.__parallel_construct()
            elif self.__split:
                (self.result_bdd, build_time) = self.__split_construct()
            else:
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
        for i in range(1,amount): 
            assignments = []
            if self.__split and not self.__split_add_all:
                assignments.append(self.result_bdd.get_solution())
            else:
                assignments = self.get_assignments(i)
    
            if len(assignments) < i:
                break
            if self.__pathing == AllRightBuilder.FixedPathType.ENCODED:
                    rsa.rsa_draw.draw_assignment_path_vars(assignments[i-1], self.result_bdd.base, self.get_simple_paths(), 
                            self.get_unique_channels(), self.__topology, file_path, failover=self.__failover)                
            else:
                rsa.rsa_draw.draw_assignment(assignments[i-1], self.result_bdd.base,self.__topology,
                                              self.__channel_data.channels, self.__channel_data.unique_channels, 
                                              self.__channel_data.overlapping_channels, file_path)
            
            if not controllable:
                time.sleep(fps)  
            else:
                input("Proceed?")
            
    
if __name__ == "__main__":
    G = topology.get_nx_graph("./topologies/japanese_topologies/kanto11.gml")
    demands = topology.get_gravity_demands2_nodes_have_constant_size(G, 2)
    print(demands)
    p = AllRightBuilder(G, demands).encoded_fixed_paths(2, AllRightBuilder.PathType.DISJOINT).sequential().limited().construct()
    p.draw(3)
    print("Don")
    print(p.result_bdd.base.count(p.result_bdd.expr))
    p.result_bdd.base.pretty_print(p.result_bdd.expr)
    
    # exit()
    # p = AllRightBuilder(G, demands).encoded_fixed_paths(3).limited().split(True).construct().draw()
    #baseline = AllRightBuilder(G, demands).encoded_fixed_paths(3).limited().construct()
    
    # print(p.result_bdd.base.bdd == baseline.result_bdd.base.bdd)
    # p.print_result()
    # pretty_print(p.result_bdd.base.bdd, p.result_bdd.expr)
    #print(baseline.size())
    #pretty_print(baseline.result_bdd.base.bdd, baseline.result_bdd.expr)  
    