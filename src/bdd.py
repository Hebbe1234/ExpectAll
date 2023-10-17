
from enum import Enum
from dd.cudd import BDD as _BDD
from dd.cudd import Function
# try:
#     from dd.cudd import BDD as _BDD
#     from dd.cudd import Function
# except ImportError:
#    # from dd.autoref import BDD as _BDD
#    # from dd.autoref import Function 
#     pass
import networkx as nx
from networkx import digraph
from networkx import MultiDiGraph
import math
from demands import Demand

def print_bdd(bdd: _BDD, expr, filename="network.svg"):
    bdd.dump(f"../out/{filename}", roots=[expr])

def get_assignments(bdd: _BDD, expr):
    return list(bdd.pick_iter(expr))

def get_assignments_block(bdd: _BDD, block):
    return get_assignments(bdd, block.expr)

def pretty_print_block(bdd: _BDD, block):
    ass = get_assignments(bdd, block.expr)
    for a in ass: 
        print(a)

def pretty_print(bdd: _BDD, expr, true_only=False, keep_false_prefix=""):
    ass: list[dict[str, bool]] = get_assignments(bdd, expr)
    for a in ass:         
        if true_only:
            a = {k:v for k,v in a.items() if v or k[0] == keep_false_prefix}
        print(dict(sorted(a.items())))

class BDD:

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

    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand], wavelengths: int = 2):
        self.bdd = _BDD()
        self.variables = []
        self.node_vars = {v:i for i,v in enumerate(topology.nodes)}
        self.edge_vars = {e:i for i,e in enumerate(topology.edges)} 
        self.demand_vars = demands
        self.encoded_node_vars :list[str]= []
        self.encoded_source_vars :list[str]= []
        self.encoded_target_vars :list[str]= []
        self.wavelengths = wavelengths
                
        self.encoding_counts = {
            BDD.ET.NODE: math.ceil(math.log2(len(self.node_vars.keys()))),
            BDD.ET.EDGE:  math.ceil(math.log2(len(self.edge_vars.keys()))),
            BDD.ET.DEMAND:  math.ceil(math.log2(len(self.demand_vars.keys()))),
            BDD.ET.PATH: len(self.edge_vars.keys()),
            BDD.ET.LAMBDA: max(1, math.ceil(math.log2(wavelengths))),
            BDD.ET.SOURCE: math.ceil(math.log2(len(self.node_vars.keys()))),
            BDD.ET.TARGET: math.ceil(math.log2(len(self.node_vars.keys()))),

        }
        self.gen_vars()

    
    def gen_vars(self):
        variable_encoding_count = math.ceil(math.log2(len(self.node_vars.keys())))
        v_bdd_vars = [f"{BDD.prefixes[BDD.ET.NODE]}{variable_encoding_count - i }" for i in range(0,variable_encoding_count)] 
        self.bdd.declare(*v_bdd_vars)

        self.encoded_node_vars = v_bdd_vars

        s_bdd_vars = [f"{BDD.prefixes[BDD.ET.SOURCE]}{variable_encoding_count - i }" for i in range(0,variable_encoding_count)] 
        self.bdd.declare(*s_bdd_vars)
        self.encoded_source_vars = s_bdd_vars

        t_bdd_vars = [f"{BDD.prefixes[BDD.ET.TARGET]}{variable_encoding_count - i }" for i in range(0,variable_encoding_count)] 
        self.bdd.declare(*t_bdd_vars)
        self.encoded_target_vars = t_bdd_vars

        edge_encoding_count = math.ceil(math.log2(len(self.edge_vars.keys())))

        e_bdd_vars = [f"{BDD.prefixes[BDD.ET.EDGE]}{edge_encoding_count - i }" for i in range(0,edge_encoding_count)] 
        self.bdd.declare(*e_bdd_vars)

        
        ee_bdd_vars = [f"{self.get_prefix_multiple(BDD.ET.EDGE, 2)}{self.encoding_counts[BDD.ET.EDGE]  - i }" for i in range(0,self.encoding_counts[BDD.ET.EDGE] )]
        self.bdd.declare(*ee_bdd_vars)

        dd_bdd_vars = [f"{BDD.prefixes[BDD.ET.DEMAND]}{self.encoding_counts[BDD.ET.DEMAND] - i}" for i in range(0,self.encoding_counts[BDD.ET.DEMAND])]
        self.bdd.declare(*dd_bdd_vars)

        d_bdd_vars = [f"{self.get_prefix_multiple(BDD.ET.DEMAND, 2)}{self.encoding_counts[BDD.ET.DEMAND] - i}" for i in range(0,self.encoding_counts[BDD.ET.DEMAND])]
        self.bdd.declare(*d_bdd_vars)

        self.declare_generic_and_specific_variables(BDD.ET.PATH, list(self.edge_vars.values()))
        self.declare_generic_and_specific_variables(BDD.ET.LAMBDA,  list(range(1, 1 + self.encoding_counts[BDD.ET.LAMBDA])))

        
        demand_encoding_count = math.ceil(math.log2(len(self.demand_vars.keys())))
        d_bdd_vars = [f"{BDD.prefixes[BDD.ET.DEMAND]}{demand_encoding_count - i}" for i in range(0,demand_encoding_count)] 
        self.bdd.declare(*d_bdd_vars)
        

    def declare_generic_and_specific_variables(self, type: ET, l: list[int]):
        bdd_vars = []
        for item in l:
            for demand in self.demand_vars.keys():
                bdd_vars.append(f"{BDD.prefixes[type]}{item}_{demand}")
                bdd_vars.append(f"{self.get_prefix_multiple(type,2)}{item}_{demand}")

        for item in l:
            bdd_vars.append(f"{BDD.prefixes[type]}{item}")
            bdd_vars.append(f"{self.get_prefix_multiple(type,2)}{item}")

        self.bdd.declare(*bdd_vars)


    def make_subst_mapping(self, l1: list[str], l2: list[str]):
        return {l1_e: l2_e for (l1_e, l2_e) in zip(l1, l2)}
    
    def get_p_var(self, edge: int, demand: (int|None) = None, override : (str|None)= None):
        if override is None:
            return f"{BDD.prefixes[BDD.ET.PATH]}{edge}{f'_{demand}' if demand is not None else ''}"
        
        return f"{override}{edge}{f'_{demand}' if demand is not None else ''}"

    def get_p_vector(self, demand: int , override: (str|None) = None):
        l1 = []
        l2 = []
        for edge in  self.edge_vars.values():
            l1.append(self.get_p_var(edge, None, override))
            l2.append(self.get_p_var(edge, demand, override))

        return self.make_subst_mapping(l1, l2)
    
    def get_lam_var(self, wavelength: int, demand: (int|None) = None, override : (str|None)= None):
        if override is  None:
            return f"{BDD.prefixes[BDD.ET.LAMBDA]}{wavelength}{f'_{demand}' if demand is not None else ''}"
        
        return f"{override}{wavelength}{f'_{demand}' if demand is not None else ''}"
        



    def get_lam_vector(self, demand: int, override : (str|None) = None):
        l1 = []
        l2 = []
        for wavelength in  range(1,self.encoding_counts[BDD.ET.LAMBDA]+1):
            l1.append(self.get_lam_var(wavelength, None, override))
            l2.append(self.get_lam_var(wavelength, demand, override))

        return self.make_subst_mapping(l1, l2)


    def compile(self):
        return self.bdd

    def get_index(self, item, type: ET):
        if type == BDD.ET.NODE:
            return self.node_vars[item]

        if type == BDD.ET.EDGE:
            return self.edge_vars[item]

        if type == BDD.ET.DEMAND:
            assert isinstance(item, int)
            return item

        return 0
    
    

    def binary_encode(self, type: ET, number: int):
        encoding_count = self.encoding_counts[type]
        encoding_expr = self.bdd.true
        for j in range(encoding_count):
            v = self.bdd.var(f"{BDD.prefixes[type]}{j+1}")
            if not (number >> (encoding_count - 1 - j)) & 1:
                v = ~v

            encoding_expr = encoding_expr & v
          
        return encoding_expr
    
    def binary_encode_as_list_of_variables(self, type: ET, number: int):
        encoding_count = self.encoding_counts[type]

        variables :list[Function]= []        
        for j in range(encoding_count):
            v = self.bdd.var(f"{BDD.prefixes[type]}{j+1}")
            if not (number >> (encoding_count - 1 - j)) & 1:
                v = ~v
            variables.append(v)
        
        return variables


    def get_prefix_multiple(self, type: ET, multiple: int):
        return "".join([BDD.prefixes[type] for _ in range(multiple)])

    def get_encoding_var_list(self, type: ET, override_prefix: (str|None) = None):
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




class Block:
    def __init__(self, base: BDD):
        self.expr = base.bdd.true


class InBlock(Block):
    def __init__(self, topology: MultiDiGraph, base: BDD):
        self.expr = base.bdd.false
        
        in_edges = [(v, topology.in_edges(v, keys=True)) for v in topology.nodes]
        for (v, edges) in in_edges:
            for e in edges:
                v_enc = base.binary_encode(BDD.ET.NODE, base.get_index(v, BDD.ET.NODE))
                e_enc = base.binary_encode(BDD.ET.EDGE, base.get_index(e, BDD.ET.EDGE))

                self.expr = self.expr | (v_enc & e_enc)

class OutBlock(Block):
    def __init__(self, topology: MultiDiGraph, base: BDD):
        out_edges = [(v, topology.out_edges(v, keys=True)) for v in topology.nodes]
        self.expr = base.bdd.false

        for (v, edges) in out_edges:
            for e in edges:
                v_enc = base.binary_encode(BDD.ET.NODE, base.get_index(v, BDD.ET.NODE))
                e_enc = base.binary_encode(BDD.ET.EDGE, base.get_index(e, BDD.ET.EDGE))

                self.expr = self.expr | (v_enc & e_enc)

class SourceBlock(Block):
    def __init__(self, base: BDD):
        self.expr = base.bdd.false

        for i, demand in base.demand_vars.items():
            v_enc = base.binary_encode(BDD.ET.NODE, base.get_index(demand.source, BDD.ET.NODE))
            d_enc = base.binary_encode(BDD.ET.DEMAND, base.get_index(i, BDD.ET.DEMAND))
            self.expr = self.expr | (v_enc & d_enc)

class TargetBlock(Block):
    def __init__(self, base: BDD):
        self.expr = base.bdd.false

        for i, demand in base.demand_vars.items():
            v_enc = base.binary_encode(BDD.ET.NODE, base.get_index(demand.target, BDD.ET.NODE))
            d_enc = base.binary_encode(BDD.ET.DEMAND, base.get_index(i, BDD.ET.DEMAND))
            self.expr = self.expr | (v_enc & d_enc)

class PassesBlock(Block):
    def __init__(self, topology: MultiDiGraph, base: BDD):
        self.expr = base.bdd.false
        for edge in topology.edges:
            e_enc = base.binary_encode(BDD.ET.EDGE, base.get_index(edge, BDD.ET.EDGE))
            p_var = base.bdd.var(base.get_p_var(base.get_index(edge, BDD.ET.EDGE)))
            self.expr = self.expr | (e_enc & p_var)

class SingleInBlock(Block):
    def __init__(self, in_b: InBlock, passes: PassesBlock, base:BDD):
        self.expr = base.bdd.true

        e_list = base.get_encoding_var_list(BDD.ET.EDGE)
        ee_list = base.get_encoding_var_list(BDD.ET.EDGE, base.get_prefix_multiple(BDD.ET.EDGE, 2))

        in_1 = in_b.expr
        in_2 = base.bdd.let(base.make_subst_mapping(e_list, ee_list), in_b.expr)

        passes_1 = passes.expr
        passes_2 = base.bdd.let(base.make_subst_mapping(e_list, ee_list), passes.expr)

        equals = base.equals(e_list, ee_list)
        u = in_1 & in_2 & passes_1 & passes_2
        v = u.implies(equals)

        self.expr = base.bdd.forall(e_list + ee_list, v)
        
class SingleOutBlock(Block):
    def __init__(self, out_b: OutBlock, passes: PassesBlock, base:BDD):
        self.expr = base.bdd.true

        e_list = base.get_encoding_var_list(BDD.ET.EDGE)
        ee_list = base.get_encoding_var_list(BDD.ET.EDGE, base.get_prefix_multiple(BDD.ET.EDGE, 2))

        out_1 = out_b.expr
        out_2 = base.bdd.let(base.make_subst_mapping(e_list, ee_list), out_b.expr)

        passes_1 = passes.expr
        passes_2 = base.bdd.let(base.make_subst_mapping(e_list, ee_list), passes.expr)

        equals = base.equals(e_list, ee_list)
        u = out_1 & out_2 & passes_1 & passes_2
        v = u.implies(equals)

        self.expr = base.bdd.forall(e_list + ee_list, v)        

class SingleWavelengthBlock(Block):
    def __init__(self, base: BDD):
        self.expr = base.bdd.false
        for i in range(base.wavelengths):
            self.expr = self.expr | base.binary_encode(BDD.ET.LAMBDA, i)

class NoClashBlock(Block):
    def __init__(self, passes: PassesBlock, base: BDD):
        self.expr = base.bdd.false

        passes_1 = passes.expr
        mappingP = {f"{BDD.prefixes[BDD.ET.PATH]}{i}": f"{base.get_prefix_multiple(BDD.ET.PATH,2)}{i}" for i in range(base.encoding_counts[BDD.ET.PATH])}
        passes_2: Function = passes.expr.let(**mappingP)
        
        l_list = base.get_encoding_var_list(BDD.ET.LAMBDA)
        ll_list =base.get_encoding_var_list(BDD.ET.LAMBDA, base.get_prefix_multiple(BDD.ET.LAMBDA, 2))
        
        d_list = base.get_encoding_var_list(BDD.ET.DEMAND)
        dd_list = base.get_encoding_var_list(BDD.ET.DEMAND, base.get_prefix_multiple(BDD.ET.DEMAND, 2))
        
        e_list = base.get_encoding_var_list(BDD.ET.EDGE)
        
        u = (passes_1 & passes_2).exist(*e_list)
        self.expr = u.implies(~base.equals(l_list, ll_list) | base.equals(d_list, dd_list))
       
class ChangedBlock(Block): 
    def __init__(self, passes: PassesBlock,  base: BDD):
        self.expr = base.bdd.true
        p_list = base.get_encoding_var_list(BDD.ET.PATH)
        pp_list = base.get_encoding_var_list(BDD.ET.PATH, base.get_prefix_multiple(BDD.ET.PATH, 2))

        passes2_subst = base.bdd.let(base.make_subst_mapping(p_list, pp_list), passes.expr)

        self.expr = self.expr & passes.expr & ( ~passes2_subst)

        # Sørger for at kun 1 bit er flippet
        only1Change = base.bdd.false
        for p in range(len(p_list)):
            p_add = base.bdd.true
            for i in range(len(p_list)):
                pi_add = base.bdd.var(p_list[i]).equiv(base.bdd.var(pp_list[i]))
                if i == p: 
                    pi_add = base.bdd.var(p_list[i]).equiv(base.bdd.true) & base.bdd.var(pp_list[i]).equiv(base.bdd.false)
                p_add = p_add & pi_add
            only1Change = only1Change | p_add
        
        self.expr = self.expr & only1Change


class TrivialBlock(Block): 
    def __init__(self, topology: MultiDiGraph,  base: BDD):
        self.expr = base.bdd.true 
        s_encoded :list[str]= base.get_encoding_var_list(BDD.ET.NODE, base.prefixes[BDD.ET.SOURCE])
        t_encoded :list[str]= base.get_encoding_var_list(BDD.ET.NODE, base.prefixes[BDD.ET.TARGET])

        self.expr = self.expr & base.equals(s_encoded, t_encoded)

        for e in topology.edges: 
            p_var :str = base.get_p_var(base.get_index(e, BDD.ET.EDGE)) 
            self.expr = self.expr & (~base.bdd.var(p_var))

class PathBlock(Block): 
    def __init__(self, topology: digraph.DiGraph, trivial : TrivialBlock, out : OutBlock, in_block : InBlock, changed: ChangedBlock, singleIn: SingleInBlock, singleOut: SingleOutBlock, base: BDD):
        path : Function = base.bdd.false #path^0
        path_prev = None

        v_list = base.get_encoding_var_list(BDD.ET.NODE)
        e_list = base.get_encoding_var_list(BDD.ET.EDGE)
        s_list = base.get_encoding_var_list(BDD.ET.SOURCE)
        pp_list = base.get_encoding_var_list(BDD.ET.PATH, base.get_prefix_multiple(BDD.ET.PATH, 2))
        p_list = base.get_encoding_var_list(BDD.ET.PATH)

        forAllSingleInOut = (singleIn.expr & singleOut.expr).forall(*v_list)
        all_exist_list :list[str]= v_list + e_list + pp_list

        out_subst = base.bdd.let(base.make_subst_mapping(v_list, s_list), out.expr)

        while path != path_prev:
            path_prev = path
            subst = {}
            subst.update(base.make_subst_mapping(p_list, pp_list))
            subst.update(base.make_subst_mapping(s_list, v_list))
            prev_temp = base.bdd.let(subst, path_prev)
                    
            myExpr = out_subst & in_block.expr & changed.expr & prev_temp 
            res = myExpr.exist(*all_exist_list) & forAllSingleInOut
            path = res | (trivial.expr)

        self.expr = path 
        

class DemandPathBlock(Block):
    def __init__(self, path : PathBlock, source : SourceBlock, target : TargetBlock, singleIn: SingleInBlock, singleOut: SingleOutBlock,  base: BDD):

        v_list = base.get_encoding_var_list(BDD.ET.NODE)
        s_list = base.get_encoding_var_list(BDD.ET.SOURCE)
        t_list = base.get_encoding_var_list(BDD.ET.TARGET)

        source_subst = base.bdd.let(base.make_subst_mapping(v_list, s_list), source.expr)
        target_subst = base.bdd.let(base.make_subst_mapping(v_list, t_list), target.expr)


        self.expr = (path.expr & source_subst & target_subst).exist(*s_list + t_list)
        

class RoutingAndWavelengthBlock(Block):
    def __init__(self, demandPath : DemandPathBlock, wavelength: SingleWavelengthBlock, noClash : NoClashBlock, numDemands :int, base: BDD):

        d_list = base.get_encoding_var_list(BDD.ET.DEMAND)
        dd_list = base.get_encoding_var_list(BDD.ET.DEMAND, base.get_prefix_multiple(BDD.ET.DEMAND, 2))
        pp_list = base.get_encoding_var_list(BDD.ET.PATH, base.get_prefix_multiple(BDD.ET.PATH, 2))
        l_list = base.get_encoding_var_list(BDD.ET.LAMBDA, base.get_prefix_multiple(BDD.ET.LAMBDA, 1))
        ll_list = base.get_encoding_var_list(BDD.ET.LAMBDA, base.get_prefix_multiple(BDD.ET.LAMBDA, 2))
        p_list = base.get_encoding_var_list(BDD.ET.PATH)


        self.expr = base.bdd.true
        fullNoClash = base.bdd.true
        d_expr = []

        for i in range(0, numDemands):
            demandPath_subst = base.bdd.let(base.get_p_vector(i),demandPath.expr)
            wavelength_subst = base.bdd.let(base.get_lam_vector(i),wavelength.expr)

            self.expr = (self.expr &  (demandPath_subst & wavelength_subst & base.binary_encode(base.ET.DEMAND, i)).exist(*(d_list+l_list)))
            noClash_subst = base.bdd.true
            
            
            for j in range(i,numDemands):
                print((i,j))
                subst = {}
                subst.update(base.get_p_vector(i))
                subst.update(base.make_subst_mapping(pp_list, list(base.get_p_vector(j).values())))

                subst.update(base.get_lam_vector(i))
                subst.update(base.make_subst_mapping(ll_list, list(base.get_lam_vector(j).values())))
                noClash_subst = base.bdd.let(subst, noClash.expr) & base.binary_encode(base.ET.DEMAND, i) & base.bdd.let(base.make_subst_mapping(d_list, dd_list), base.binary_encode(base.ET.DEMAND, j)) 
                d_expr.append(noClash_subst.exist(*(d_list + dd_list)))
                #self.expr = (self.expr & noClash_subst).exist(*(d_list + dd_list))
        
        for i in range(0, len(d_expr),3):
            print(f"{i}/{len(d_expr)}")
            d_e1 = d_expr[i]
            d_e2 = d_expr[i+1]
            d_e3 = d_expr[i+2]
            d_e = d_e1 & d_e2 & d_e3 
            self.expr = (self.expr & d_e)

from timeit import default_timer as timer

class RWAProblem:
    def __init__(self, G: MultiDiGraph, demands: dict[int, Demand], wavelengths: int):
        s = timer()
        self.base = BDD(G, demands, wavelengths)

        in_expr = InBlock(G, self.base)
        out_expr = OutBlock(G, self.base)
        source = SourceBlock(self.base)
        target = TargetBlock( self.base)
        trivial_expr = TrivialBlock(G, self.base)
        passes_expr = PassesBlock(G, self.base)
        singleIn = SingleInBlock(in_expr, passes_expr, self.base)
        singleOut = SingleOutBlock(out_expr, passes_expr, self.base)

        passes = PassesBlock(G, self.base)
        changed = ChangedBlock(passes, self.base)
        path = PathBlock(G, trivial_expr, out_expr,in_expr, changed, singleIn, singleOut, self.base)
        demandPath = DemandPathBlock(path,source,target,singleIn, singleOut,self.base)
        singleWavelength_expr = SingleWavelengthBlock(self.base)
        noClash_expr = NoClashBlock(passes_expr, self.base) 
        print(demandPath.expr.count())

        e1 = timer()
        print(e1 - s, flush=True)
        
        self.rwa = RoutingAndWavelengthBlock(demandPath, singleWavelength_expr, noClash_expr, len(demands), self.base )
        e2 = timer()
        print(e2 - s, flush=True)
        
    def get_assignments(self):
        return get_assignments(self.base.bdd, self.rwa.expr)
    
    def print_assignments(self, true_only=False, keep_false_prefix=""):
        pretty_print(self.base.bdd, self.rwa.expr, true_only, keep_false_prefix=keep_false_prefix)
        
if __name__ == "__main__":
    pass
    # G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/simple_net.dot"))
    # if G.nodes.get("\\n") is not None:
    #     G.remove_node("\\n")

    # demands = {0: Demand("A", "B"),1: Demand("C", "B")}
    # RWAProblem(G, demands, 3)
    #print(base.bdd.vars)

    # print(get_assignments_block(base.bdd, trivial_expr))
    # source_expr = SourceBlock(base)
    # target_expr = TargetBlock(base)
    # singleIn_expr = SingleInBlock(in_expr, passes_expr, base)
    # singleOut_expr = SingleOutBlock(out_expr, passes_expr, base)
  

    # print(len(get_assignments(base.bdd, trivial_expr.expr)))
  
    # d_list = base.get_encoding_var_list(BDD.ET.DEMAND)
    # dd_list = base.get_encoding_var_list(BDD.ET.DEMAND, base.get_prefix_multiple(BDD.ET.DEMAND, 2))
        
    # u: Function = noClash_expr.expr.forall(*(d_list + dd_list))
    # print(noClash_expr.expr.count())
    # print(u.count())
    
    # x = (noClash_expr.expr & ~base.bdd.var("d1") & base.bdd.var("dd1") & base.bdd.var("l1") & base.bdd.var("ll1"))
    # print((x.exist(*(["d1", "dd1", "l1", "ll1"]))).count())
    # print(get_assignments(base.bdd, u))
    # print(get_assignments(base.bdd, x.exist(*(["d1", "dd1", "l1", "ll1"]))))
  
