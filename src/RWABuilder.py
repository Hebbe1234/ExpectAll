from enum import Enum
from networkx import MultiDiGraph
from demands import Demand
from niceBDD import *
from niceBDDBlocks import ChannelFullNoClashBlock, ChannelNoClashBlock, ChannelOverlap, ChannelSequentialBlock, CliqueWavelengthsBlock, DynamicAddBlock, ChangedBlock, DemandPathBlock, EncodedFixedPathBlock, FixedPathBlock, FullNoClashBlock, InBlock, NoClashBlock, OnlyOptimalBlock, OutBlock, OverlapsBlock, PassesBlock, PathBlock, RoutingAndChannelBlock, RoutingAndWavelengthBlock, SequenceWavelengthsBlock, SingleOutBlock, SingleWavelengthBlock, SourceBlock, SplitAddAllBlock, SplitAddBlock, TargetBlock, TrivialBlock
import topology

class AllRightBuilder:
    
    class FixedPathType(Enum):
        DEFAULT=0
        NAIVE=1
        ENCODED=2
    
    class PathType(Enum):
        DEFAULT=0
        DISJOINT=1
        SHORTEST=2
    
    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand], wavelengths = 0):
        self.__topology = topology
        self.__demands = demands
        self.__wavelengths = wavelengths 
        self.__inc = False 
        
        self.__dynamic = False
        self.__dynamic_max_demands = 128
        
        self.__lim = False
        self.__seq = False
        self.__cliq = False 
        
        self.__static_order = [ET.EDGE, ET.LAMBDA, ET.NODE, ET.DEMAND, ET.TARGET, ET.PATH, ET.SOURCE]
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
        
        
        self.__rsa = False
        self.__channels = {}
        self.__overlapping_channels = []
        self.__unique_channels = []
        self.__connected_channels = {}
        self.__number_of_slots = 0
        
    def get_channels(self):
        return self.__channels
    
    def get_unique_channels(self):
        return self.__unique_channels
    
    def get_overlapping_channels(self):
        return self.__overlapping_channels
    
    def get_demands(self):
        return self.__demands
    
    def get_build_time(self):
        return self.__build_time
      
    def dynamic(self, max_demands = 128):
        self.__dynamic = True
        self.__dynamic_max_demands = max_demands
        return self
    
    def limited(self): 
        self.__lim = True
        return self
    
    def sequential(self): 
        if self.__rsa:
            assert len(self.__unique_channels) > 0
            self.__channels = topology.get_channels(self.__demands, number_of_slots=self.__number_of_slots,limit=True)
            self.__overlapping_channels, self.__unique_channels = topology.get_overlapping_channels(self.__channels)
            self.__connected_channels = topology.get_connected_channels(self.__unique_channels)
        
        self.__seq = True
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
        
        return self
    
    def pruned(self):
        assert self.__paths == [] # Pruning must be done before paths are found
        assert self.__subgraphs == [] # Pruning must be done before the graph is split

        self.__topology = topology.reduce_graph_based_on_demands(self.__topology, self.__demands)
        return self

    def increasing(self):
        self.__inc = True
        return self
    
    def channels(self, number_of_slots=64):
        self.__rsa = True
        self.__static_order = [ET.EDGE, ET.CHANNEL, ET.NODE, ET.DEMAND, ET.TARGET, ET.PATH, ET.SOURCE]
        self.__number_of_slots = number_of_slots
        self.__channels = topology.get_channels(self.__demands, number_of_slots=number_of_slots, limit=self.__lim)
        self.__overlapping_channels, self.__unique_channels = topology.get_overlapping_channels(self.__channels)
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
            channels = topology.get_channels(self.__demands, number_of_slots=slots, limit=self.__lim)
            overlapping_channels, unique_channels = topology.get_overlapping_channels(channels)
            connected_channels = topology.get_connected_channels(unique_channels)

            base = ChannelBDD(self.__topology, self.__demands, self.__static_order, channels, unique_channels, 
                            overlapping_channels, connected_channels = connected_channels, reordering=self.__reordering)
            
            (rs, build_time) = self.__build_rsa(base)
            times.append(build_time)
            
            assert rs != None

            if rs.expr != rs.expr.bdd.false:
                return (rs, max(times))
            
        return (rs, max(times))
      

    def __increasing_construct(self):
        assert self.__wavelengths > 0
        times = []

        for w in range(1,self.__wavelengths+1):
            rw = None
            if self.__dynamic:
                (rw, build_time) = self.__parallel_construct(w)
            
            elif self.__split:
                (rw, build_time) = self.__split_construct(w)
            
            elif not self.__dynamic and (self.__pathing == AllRightBuilder.FixedPathType.DEFAULT or self.__pathing == AllRightBuilder.FixedPathType.NAIVE):
                base = DefaultBDD(self.__topology, self.__demands, self.__static_order, w, reordering=self.__reordering)        
                (rw, build_time) = self.__build_rwa(base)
            
            elif not self.__dynamic and self.__pathing == AllRightBuilder.FixedPathType.ENCODED:
                base = DefaultBDD(self.__topology, self.__demands, self.__static_order,w, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths, encoded_paths=True)
                (rw, build_time) = self.__build_rwa(base)
          
            times.append(build_time)
            
            assert rw != None

            if not self.__split and rw.expr != rw.expr.bdd.false:
                return (rw, max(times))
            elif self.__split and not self.__split_add_all and rw.validSolutions:
                return (rw, max(times))
            
        return (rw, max(times))
        
    def __parallel_construct(self, w=-1):
        rws = []
        rws_next = []
        n = 1
        
        times = {0:[]}

        for i in range(0, len(self.__demands), n):
            base = DynamicBDD(self.__topology, {k:d for k,d in self.__demands.items() if i * n <= k and k < i * n + n }, self.__static_order, self.__wavelengths if w == -1 else w, init_demand=i*n, max_demands=self.__dynamic_max_demands, reordering=self.__reordering)
            (rw, build_time) = self.__build_rwa(base)
            rws.append((rw, base))
            times[0].append(build_time)
        
        while len(rws) > 1:
            times[len(times)] = []

            rws_next = []
            for i in range(0, len(rws), 2):
                if i + 1 >= len(rws):
                    rws_next.append(rws[i])
                    break
                
                start_time = time.perf_counter()

                add_block = DynamicAddBlock(rws[i][0],rws[i+1][0], rws[i][1], rws[i+1][1])
                rws_next.append((add_block, add_block.base))

                times[len(times) - 1].append(time.perf_counter() - start_time)

            rws = rws_next
        
        full_time = 0
        for k in times:
            full_time += max(times[k])
                    
        return (rws[0][0], full_time)
    
    def __split_construct(self, w=-1):
        assert self.__split and self.__subgraphs is not None
        solutions = []
        
        times = []
        
        for g in self.__subgraphs: 
            if g in self.__graph_to_new_demands:
                demands = self.__graph_to_new_demands[g]
                base = SplitBDD(g, demands, self.__static_order,  self.__wavelengths if w == -1 else w, reordering=self.__reordering)
                (rw1, build_time) = self.__build_rwa(base, g)
                times.append(build_time)
                solutions.append(rw1)
                
        start_time_add = time.perf_counter() 
        if self.__split_add_all:
            return (SplitAddAllBlock(self.__topology, solutions, self.__old_demands, self.__graph_to_new_demands), time.perf_counter() - start_time_add + max(times))
        else:
            return (SplitAddBlock(self.__topology, solutions, self.__old_demands, self.__graph_to_new_demands), time.perf_counter() - start_time_add + max(times))

    def __build_rwa(self, base, subgraph=None):
        start_time = time.perf_counter()

        source = SourceBlock(base)
        target = TargetBlock(base)
        
        G = self.__topology if subgraph == None else subgraph
        
        path = base.bdd.true 
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
            path = EncodedFixedPathBlock(self.__paths, base)
            

        demandPath = DemandPathBlock(path, source, target, base)
        singleWavelength_expr = SingleWavelengthBlock(base)
        
        noClash_expr = base.bdd.true
        if self.__pathing == AllRightBuilder.FixedPathType.ENCODED:
            noClash_expr = ~(OverlapsBlock(base).expr)
        else:
            noClash_expr = NoClashBlock(passes, base).expr
       

        rwa = RoutingAndWavelengthBlock(demandPath, singleWavelength_expr, base, constrained=self.__lim)

        if self.__cliq:
            rwa.expr = CliqueWavelengthsBlock(rwa, self.__cliques, base).expr

        if self.__seq:
            rwa.expr = SequenceWavelengthsBlock(rwa, base).expr
  
        fullNoClash = FullNoClashBlock(rwa.expr, noClash_expr, base)
        
        if self.__only_optimal:
            fullNoClash.expr = OnlyOptimalBlock(fullNoClash.expr, base).expr

        return (fullNoClash, time.perf_counter() - start_time)
    
    def __build_rsa(self, base, subgraph=None):
        assert self.__pathing != AllRightBuilder.FixedPathType.ENCODED # We have not implemented encoded paths yet
        assert self.__rsa
        
        start_time = time.perf_counter()

        source = SourceBlock(base)
        target = TargetBlock(base)
        
        G = self.__topology if subgraph == None else subgraph
        
        path = base.bdd.true 
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
            
        demandPath = DemandPathBlock(path, source, target, base)
        
        overlap = ChannelOverlap(base)
        
        noClash_expr = base.bdd.true
        noClash_expr = ChannelNoClashBlock(passes, overlap, base)
        
        print("sequential...")
        sequential = base.bdd.true
        if self.__seq:
            sequential = ChannelSequentialBlock(base).expr
        print("sequential computed")
        
        rsa = RoutingAndChannelBlock(demandPath, base, limit=self.__lim)
        fullNoClash = ChannelFullNoClashBlock(rsa.expr & sequential, noClash_expr, base)
        
        return (fullNoClash, time.perf_counter() - start_time)
    
    def construct(self):
        assert not (self.__dynamic & (self.__pathing != AllRightBuilder.FixedPathType.DEFAULT))
        assert not (self.__cliq & (self.__pathing == AllRightBuilder.FixedPathType.DEFAULT))
        assert not (self.__dynamic & self.__seq)
        assert not (self.__split & self.__seq)
        assert not (self.__split & self.__only_optimal)
        assert not (not self.__rsa & self.__wavelengths == 0)

        base = None
        if not self.__rsa:
            if not self.__dynamic and (self.__pathing == AllRightBuilder.FixedPathType.DEFAULT or self.__pathing == AllRightBuilder.FixedPathType.NAIVE):
                base = DefaultBDD(self.__topology, self.__demands, self.__static_order, self.__wavelengths, reordering=self.__reordering)
            
            elif not self.__dynamic and self.__pathing == AllRightBuilder.FixedPathType.ENCODED:
                base = DefaultBDD(self.__topology, self.__demands, self.__static_order, self.__wavelengths, reordering=self.__reordering, paths=self.__paths, overlapping_paths=self.__overlapping_paths,encoded_paths=True)
        
        
        if self.__rsa:
            if self.__inc: 
                (self.result_bdd, build_time) = self.__channel_increasing_construct()
            else: 
                base = ChannelBDD(self.__topology, self.__demands, self.__static_order, self.__channels, self.__unique_channels, 
                                self.__overlapping_channels, reordering=self.__reordering, connected_channels=self.__connected_channels)
                (self.result_bdd, build_time) = self.__build_rsa(base)
        elif self.__inc:
            (self.result_bdd, build_time) = self.__increasing_construct()
        else:
            if self.__dynamic:
                (self.result_bdd, build_time) = self.__parallel_construct()
            elif self.__split:
                (self.result_bdd, build_time) = self.__split_construct()
            else:
                (self.result_bdd, build_time) = self.__build_rwa(base)

        self.__build_time = build_time
        assert self.result_bdd != None
        
        return self
    
    def solved(self):
        return self.result_bdd.expr != self.result_bdd.base.bdd.false
    
    def size(self):
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
    
if __name__ == "__main__":
    G = topology.get_nx_graph(topology.TOPZOO_PATH +  "/Grena.gml")
    demands = topology.get_gravity_demands(G, 10,seed=7)
    print(demands)
    exit()
    p = AllRightBuilder(G, demands).channels(4).limited().increasing().construct()
    p.print_result()
    pretty_print(p.result_bdd.base.bdd, p.result_bdd.expr)  