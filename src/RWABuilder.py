from enum import Enum
from networkx import MultiDiGraph
from demands import Demand
from niceBDD import *
from niceBDDBlocks import AddBlock, ChangedBlock, DemandPathBlock, FullNoClashBlock, InBlock, NoClashBlock, OnlyOptimalBlock, OutBlock, PassesBlock, PathBlock, RoutingAndWavelengthBlock, SequenceWavelengthsBlock, SingleOutBlock, SingleWavelengthBlock, SourceBlock, TargetBlock, TrivialBlock
import topology

class RWABuilder:
    
    class PathType(Enum):
        DEFAULT=0
        NAIVE=1
        ENCODED=2
        DISJOINT_ENCODED=3
        SHORTESTS_ENCODED=4
    
    
    
    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand], wavelengths = 2):
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

        self.__pathing = RWABuilder.PathType.DEFAULT
        self.__only_optimal = False
        
    def conquer(self, max_demands = 128):
        self.__dynamic = True
        self.__dynamic_max_demands = max_demands
        return self
    
    def limited(self): 
        self.__lim = True
        return self
    
    def sequential(self): 
        self.__seq = True
        return self
    
    def clique(self): 
        self.__cliq = True
        return self
    
    def order(self, new_order):
        assert len(self.__static_order) == len(new_order)
        self.__static_order = new_order
        return self
    
    def optimal(self):
        self.__only_optimal = True
        return self
    
    def increasing(self):
        self.__inc = True
        return self
    
    def __increasing_construct(self):
        assert self.__wavelengths > 0
        for w in range(1,self.__wavelengths+1):
            rw = None
            if self.__dynamic:
                rw = self.__parallel_construct()
            else:
                base = DefaultBDD(self.__topology, self.__demands, self.__static_order, w, reordering=True)
                rw = self.__build_rwa(base)
           
            assert rw != None

            if rw != rw.expr.bdd.false:
                return rw.expr

        return rw.expr
        
    def __parallel_construct(self, w=-1):
        rws = []
        rws_next = []
        n = 1
        for i in range(0, len(self.__demands), n):
            base = DynamicBDD(self.__topology, {k:d for k,d in self.__demands.items() if i * n <= k and k < i * n + n }, self.__static_order, self.__wavelengths if w != -1 else w, init_demand=i*n, max_demands=self.__dynamic_max_demands)
            rws.append(self.__build_rwa(base))
        
        while len(rws) > 1:
            rws_next = []
            for i in range(0, len(rws), 2):
                if i + 1 >= len(rws):
                    rws_next.append(rws[i])
                    break
                rws_next.append(AddBlock(rws[i],rws[i+1]))
            
            rws = rws_next
        
   
        return rws[0]
    
    def __build_rwa(self, base):
        source = SourceBlock(base)
        target = TargetBlock(base)
        
        path = base.bdd.true 
        print("H1")
        if self.__pathing == RWABuilder.PathType.DEFAULT:
            print("H1.2")
            passes = PassesBlock(self.__topology, base)
            print("H1.3")

            in_expr = InBlock(self.__topology, base)
            out_expr = OutBlock(self.__topology, base)
            print("H1.4")
            
            trivial_expr = TrivialBlock(self.__topology, base)
            singleOut = SingleOutBlock(out_expr, passes, base)
            print("H1.5")
            changed = ChangedBlock(passes, base)
            print("H1.5")

            path = PathBlock(trivial_expr, out_expr,in_expr, changed, singleOut, base)
        print("H2")

        demandPath = DemandPathBlock(path, source, target, base)
        singleWavelength_expr = SingleWavelengthBlock(base)
            
        noClash_expr = NoClashBlock(passes, base) 
        rwa = RoutingAndWavelengthBlock(demandPath, singleWavelength_expr, base, constrained=self.__lim)
        print("H3")

        sequenceWavelengths = base.bdd.true
        if self.__seq:
            sequenceWavelengths = SequenceWavelengthsBlock(rwa, base)
        
        
        cliquePruning = base.bdd.true
        if self.__cliq:
            pass
            # cliques = topology.get_overlap_cliques(list(self.demands.values()), paths)
            # cliquePruning = Clique(rwa, base)
        
        full = rwa.expr 
        
        if self.__seq:
            full = full & sequenceWavelengths.expr    
    
        fullNoClash = FullNoClashBlock(full, noClash_expr, base)
        
        return fullNoClash

    
    def construct(self):
        assert not (self.__dynamic & (self.__pathing != RWABuilder.PathType.DEFAULT))
        assert not (self.__cliq & (self.__pathing == RWABuilder.PathType.DEFAULT))
        assert not (self.__dynamic & self.__seq)
        assert not (self.__seq & self.__cliq)

        base = None
        if not self.__dynamic and self.__pathing == RWABuilder.PathType.DEFAULT:
            base = DefaultBDD(self.__topology, self.__demands, self.__static_order, self.__wavelengths, reordering=True)
        
        assert base != None
        
        if self.__inc:
            self.rwa = self.__increasing_construct()
        else:
            if self.__dynamic:
                self.rwa = self.__parallel_construct()
            else:
                self.rwa = self.__build_rwa(base)

        assert self.rwa != None
        
        if self.__only_optimal:
            only_optimal = OnlyOptimalBlock(self.rwa, base)
            self.rwa = only_optimal.expr

        return self
    
if __name__ == "__main__":
    G = topology.get_nx_graph(topology.TOPZOO_PATH +  "/Ai3.gml")
    demands = topology.get_demands(G, 5,seed=3)

    p = RWABuilder(G, demands, 2).construct()
        