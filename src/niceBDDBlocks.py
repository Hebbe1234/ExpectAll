from enum import Enum
import time
from typing import Callable

from niceBDD import BaseBDD, ET, DynamicBDD, SplitBDD, prefixes

has_cudd = False

try:
    # raise ImportError()
    from dd.cudd import BDD as _BDD
    from dd.cudd import Function
    has_cudd = True
except ImportError:
   from dd.autoref import BDD as _BDD
   from dd.autoref import Function 
   print("Using autoref... ")

from networkx import MultiDiGraph
import math
from demands import Demand
from itertools import permutations


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


def iben_print(bdd: _BDD, expr, true_only=False, keep_false_prefix=""):
    ass: list[dict[str, bool]] = get_assignments(bdd, expr)
    for a in ass:         
        if true_only:
            a = {k:v for k,v in a.items() if v or k[0] == keep_false_prefix}
        print(dict(sorted(a.items())))

    for i, a in enumerate(ass):
        st = f"st{i} := "
        for k,v in sorted(a.items()):
            st += (f"{'!' if v == False else ''}{k} &")
        print(st[:-1])
        
class InBlock():
    def __init__(self, topology: MultiDiGraph, base):
        self.expr = base.bdd.false
        
        in_edges = [(v, topology.in_edges(v, keys=True)) for v in topology.nodes]
        for (v, edges) in in_edges:
            for e in edges:
                v_enc = base.encode(ET.NODE, base.get_index(v, ET.NODE))
                e_enc = base.encode(ET.EDGE, base.get_index(e, ET.EDGE))

                self.expr = self.expr | (v_enc & e_enc)

class OutBlock():
    def __init__(self, topology: MultiDiGraph, base):
        out_edges = [(v, topology.out_edges(v, keys=True)) for v in topology.nodes]
        self.expr = base.bdd.false

        for (v, edges) in out_edges:
            for e in edges:
                v_enc = base.encode(ET.NODE, base.get_index(v, ET.NODE))
                e_enc = base.encode(ET.EDGE, base.get_index(e, ET.EDGE))

                self.expr = self.expr | (v_enc & e_enc)

class SourceBlock():
    def __init__(self, base):
        self.expr = base.bdd.false

        for i, demand in base.demand_vars.items():
            v_enc = base.encode(ET.NODE, base.get_index(demand.source, ET.NODE))
            d_enc = base.encode(ET.DEMAND, base.get_index(i, ET.DEMAND))
            self.expr = self.expr | (v_enc & d_enc)

class TargetBlock():
    def __init__(self, base):
        self.expr = base.bdd.false

        for i, demand in base.demand_vars.items():
            v_enc = base.encode(ET.NODE, base.get_index(demand.target, ET.NODE))
            d_enc = base.encode(ET.DEMAND, base.get_index(i, ET.DEMAND))
            self.expr = self.expr | (v_enc & d_enc)

class PassesBlock():
    def __init__(self, topology: MultiDiGraph, base):
        self.expr = base.bdd.false
        for edge in topology.edges:
            e_enc = base.encode(ET.EDGE, base.get_index(edge, ET.EDGE))
            p_var = base.bdd.var(base.get_p_var(base.get_index(edge, ET.EDGE)))
            self.expr = self.expr | (e_enc & p_var)

class SingleOutBlock():
    def __init__(self, out_b: OutBlock, passes: PassesBlock, base:BaseBDD):
        self.expr = base.bdd.true

        e_list = base.get_encoding_var_list(ET.EDGE)
        ee_list = base.get_encoding_var_list(ET.EDGE, base.get_prefix_multiple(ET.EDGE, 2))

        out_1 = out_b.expr
        out_2 = base.bdd.let(base.make_subst_mapping(e_list, ee_list), out_b.expr)

        passes_1 = passes.expr
        passes_2 = base.bdd.let(base.make_subst_mapping(e_list, ee_list), passes.expr)

        equals = base.equals(e_list, ee_list)
        u = out_1 & out_2 & passes_1 & passes_2
        v = u.implies(equals)

        self.expr = base.bdd.forall(e_list + ee_list, v)      
        

class ChangedBlock(): 
    def __init__(self, passes: PassesBlock,  base):
        self.expr = base.bdd.true
        p_list = base.get_encoding_var_list(ET.PATH)
        pp_list = base.get_encoding_var_list(ET.PATH, base.get_prefix_multiple(ET.PATH, 2))

        passes2_subst = base.bdd.let(base.make_subst_mapping(p_list, pp_list), passes.expr)

        self.expr = self.expr & passes.expr & ( ~passes2_subst)

        # Only one bit is flipped
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


class TrivialBlock(): 
    def __init__(self, topology: MultiDiGraph,  base):
        self.expr = base.bdd.true 
        s_encoded :list[str]= base.get_encoding_var_list(ET.NODE, prefixes[ET.SOURCE])
        t_encoded :list[str]= base.get_encoding_var_list(ET.NODE, prefixes[ET.TARGET])

        self.expr = self.expr & base.equals(s_encoded, t_encoded)

        for e in topology.edges: 
            p_var :str = base.get_p_var(base.get_index(e, ET.EDGE)) 
            self.expr = self.expr & (~base.bdd.var(p_var))

class PathBlock(): 
    def __init__(self, trivial : TrivialBlock, out : OutBlock, in_block : InBlock, changed: ChangedBlock, singleOut: SingleOutBlock, base):
        path : Function = trivial.expr #path^0
        path_prev = None

        v_list = base.get_encoding_var_list(ET.NODE)
        e_list = base.get_encoding_var_list(ET.EDGE)
        s_list = base.get_encoding_var_list(ET.SOURCE)
        t_list = base.get_encoding_var_list(ET.TARGET)
        pp_list = base.get_encoding_var_list(ET.PATH, base.get_prefix_multiple(ET.PATH, 2))
        p_list = base.get_encoding_var_list(ET.PATH)

        singleOutSource = base.bdd.let(base.make_subst_mapping(v_list, s_list), singleOut.expr)

        all_exist_list :list[str]= v_list + e_list + pp_list

        out_subst = base.bdd.let(base.make_subst_mapping(v_list, s_list), out.expr)

        while path != path_prev:
            path_prev = path
            subst = {}
            subst.update(base.make_subst_mapping(p_list, pp_list))
            subst.update(base.make_subst_mapping(s_list, v_list))
            prev_temp = base.bdd.let(subst, path_prev)
                    
            myExpr = out_subst & in_block.expr & ~base.equals(s_list, t_list) & changed.expr & prev_temp 
            res = myExpr.exist(*all_exist_list) & singleOutSource
            path = res | (trivial.expr) #path^k 

        self.expr = path 
        
class FixedPathBlock():
    def __init__(self, paths, base):
        self.expr = base.bdd.false
        p_list = base.get_encoding_var_list(ET.PATH)
        
        for path in paths:
            s_expr = base.encode(ET.SOURCE, base.get_index(path[0][0], ET.NODE))
            t_expr = base.encode(ET.TARGET, base.get_index(path[-1][1], ET.NODE))
            p_expr = s_expr & t_expr
            
            edges_in_path = []
            
            for edge in path:
                i = base.get_index(edge, ET.EDGE)
                p_expr &= base.bdd.var(p_list[i]).equiv(base.bdd.true)
                edges_in_path.append(i)
            
            for edge in range(len(p_list)):
                if edge not in edges_in_path:
                    p_expr &= base.bdd.var(p_list[edge]).equiv(base.bdd.false)
            
            self.expr |= p_expr

class EncodedFixedPathBlock():
    def __init__(self, paths, base):
        self.expr = base.bdd.false

        for i, path in enumerate(paths):
            s_expr = base.encode(ET.SOURCE, base.get_index(path[0][0], ET.NODE))
            t_expr = base.encode(ET.TARGET, base.get_index(path[-1][1], ET.NODE))
            path_expr = base.encode(ET.PATH, i)
            
            p_expr = (s_expr & t_expr & path_expr)

            self.expr |= p_expr

class EncodedFixedPathBlockSplit():
    def __init__(self, paths, base):
        self.expr = base.bdd.false

        for i, path in (paths):
            s_expr = base.encode(ET.SOURCE, base.get_index(path[0][0], ET.NODE))
            t_expr = base.encode(ET.TARGET, base.get_index(path[-1][1], ET.NODE))
            path_expr = base.encode(ET.PATH, i)
            
            p_expr = (s_expr & t_expr & path_expr)

            self.expr |= p_expr


class DemandPathBlock():
    def __init__(self, path, source : SourceBlock, target : TargetBlock, base):

        v_list = base.get_encoding_var_list(ET.NODE)
        s_list = base.get_encoding_var_list(ET.SOURCE)
        t_list = base.get_encoding_var_list(ET.TARGET)

        source_subst = base.bdd.let(base.make_subst_mapping(v_list, s_list), source.expr)
        target_subst = base.bdd.let(base.make_subst_mapping(v_list, t_list), target.expr)


        self.expr = (path.expr & source_subst & target_subst).exist(*s_list + t_list)  




class PathOverlapsBlock():
    def __init__(self, base: BaseBDD):
        p_list = base.get_encoding_var_list(ET.PATH)
        pp_list = base.get_encoding_var_list(ET.PATH, base.get_prefix_multiple(ET.PATH, 2))
        
        self.expr = base.bdd.false
        
        for (i, j) in base.overlapping_paths:
            path1 = base.encode(ET.PATH, i)
            path2 = base.bdd.let(base.make_subst_mapping(p_list, pp_list), base.encode(ET.PATH, j))           
            self.expr |= (path1 & path2)
 

class ChannelOverlap():
    def __init__(self, base: BaseBDD):
        self.expr = base.bdd.false

        c_list = base.get_encoding_var_list(ET.CHANNEL)
        cc_list = base.get_encoding_var_list(ET.CHANNEL, base.get_prefix_multiple(ET.CHANNEL, 2))

        for (c1, c2) in base.overlapping_channels:
            c1_var = base.encode(ET.CHANNEL, c1)
            c2_var = base.bdd.let(base.make_subst_mapping(c_list, cc_list), base.encode(ET.CHANNEL, c2))
            
            self.expr |= c1_var & c2_var
            
class EncodedChannelNoClashBlock():
    def __init__(self, pathOverLap: PathOverlapsBlock, channelOverlap: ChannelOverlap, base: BaseBDD):
        self.expr = base.bdd.false
        d_list = base.get_encoding_var_list(ET.DEMAND)
        dd_list = base.get_encoding_var_list(ET.DEMAND, base.get_prefix_multiple(ET.DEMAND, 2))

        self.expr = base.equals(d_list,dd_list) | ~pathOverLap.expr | ~channelOverlap.expr

class ChannelNoClashBlock():
    def __init__(self, passes: PassesBlock, channelOverlap: ChannelOverlap, base: BaseBDD):
        self.expr = base.bdd.false

        passes_1 = passes.expr
        mappingP = {}
        for e in list(base.edge_vars.values()):
            mappingP.update({f"{prefixes[ET.PATH]}{e}": f"{base.get_prefix_multiple(ET.PATH,2)}{e}"})
        
        passes_2: Function = passes.expr.let(**mappingP)
        
        c_list = base.get_encoding_var_list(ET.CHANNEL)
        cc_list =base.get_encoding_var_list(ET.CHANNEL, base.get_prefix_multiple(ET.CHANNEL, 2))
        
        d_list = base.get_encoding_var_list(ET.DEMAND)
        dd_list = base.get_encoding_var_list(ET.DEMAND, base.get_prefix_multiple(ET.DEMAND, 2))
        
        e_list = base.get_encoding_var_list(ET.EDGE)
        
        u = (passes_1 & passes_2).exist(*(e_list + c_list + cc_list))
        self.expr = u.implies(~channelOverlap.expr | base.equals(d_list, dd_list))


class DynamicFullNoClash():
    def __init__(self, demands1: dict[int,Demand], demands2: dict[int,Demand], noClash: ChannelNoClashBlock, base: DynamicBDD, init: Function):
        self.expr = init
        self.base = base

        d_list = base.get_encoding_var_list(ET.DEMAND)
        dd_list = base.get_encoding_var_list(ET.DEMAND, base.get_prefix_multiple(ET.DEMAND, 2))
        pp_list = base.get_encoding_var_list(ET.PATH, base.get_prefix_multiple(ET.PATH, 2))
        cc_list = base.get_encoding_var_list(ET.CHANNEL, base.get_prefix_multiple(ET.CHANNEL, 2))
        
        d_expr = []


        for i in demands1.keys():
            noClash_subst = base.bdd.true

            for j in demands2.keys():

                subst = {}
                subst.update(base.get_p_vector(i))
                subst.update(base.make_subst_mapping(pp_list, list(base.get_p_vector(j).values())))

                subst.update(base.get_channel_vector(i))
                subst.update(base.make_subst_mapping(cc_list, list(base.get_channel_vector(j).values())))
                noClash_subst = base.bdd.let(subst, noClash.expr) & base.encode(ET.DEMAND, i) & base.bdd.let(base.make_subst_mapping(d_list, dd_list), base.encode(ET.DEMAND, j)) 
                d_expr.append(noClash_subst.exist(*(d_list + dd_list)))
        
        i_l = 0
        
        for j in range(i_l, len(d_expr)):
            
            # print(f"{j}/{len(d_expr)}")
            d_e = d_expr[j] 
            self.expr = self.expr & d_e


        
class DynamicAddBlock():
    def __init__(self, rwa1, rwa2, base1, base2):
        if not base1.topology == base2.topology:
            raise ValueError("Topologies not equal")
        if  max([0] + list(base1.demand_vars.keys())) != (min(list(base2.demand_vars.keys()))-1):
            print(base1.demand_vars)
            print(base2.demand_vars)
            raise ValueError("Demands keys are not directly sequential")

        demands = {}
        demands.update(base1.demand_vars)
        demands.update(base2.demand_vars)

        self.base = DynamicBDD(base1.topology,demands, base1.channel_data, base1.ordering,  init_demand = min(list(base1.demand_vars.keys())))
        old_assignments = base1.bdd.copy(rwa1.expr, self.base.bdd)
        
        new_assignments = base2.bdd.copy(rwa2.expr, self.base.bdd)
        channel_overlap = ChannelOverlap(self.base)
        print(f"channel_overlap", channel_overlap.expr == self.base.bdd.false)

        passes=PassesBlock(base1.topology,self.base)
        print(f"PASSES", passes.expr == self.base.bdd.false)

        noclash=ChannelNoClashBlock(passes,channel_overlap, self.base )
        print(f"noclash", noclash.expr == self.base.bdd.false)

        dynamicNoClash = DynamicFullNoClash(base1.demand_vars, base2.demand_vars, noclash, self.base, old_assignments & new_assignments)

        self.expr = (dynamicNoClash.expr)
 

class SplitAddBlock():
    def __init__(self, G, rsa_list:list, demands:dict[int,Demand], graphToDemands):
        self.base = SplitBDD(G, demands, rsa_list[0].base.ordering,  rsa_list[0].base.channel_data, rsa_list[0].base.reordering)
        self.expr = self
        
        rsa_to_demands = {}
        self.validSolutions = True
        #make dict from rwa_problem to demnads
        for (rsa, (_, graph_demands)) in zip(rsa_list, graphToDemands.items()):
            rsa_to_demands[rsa] = graph_demands.keys()
        
        self.rsa_to_demands = rsa_to_demands
        # 'and' all subproblems' wavelengths together based on demands they share
        for rsa1, demands1 in rsa_to_demands.items():
            for rsa2, demands2 in rsa_to_demands.items():
                if rsa1 == rsa2:
                    continue
                
                shared_demands = list(set(demands1).intersection(set(demands2)))
                if shared_demands == []:
                    continue
                
                #exist variables away they do not share and 'and' remaining expression
                variables_to_keep = [list(rsa1.base.get_channel_vector(d).values()) for d in shared_demands] + [list(rsa1.base.get_channel_vector(d,self.base.get_prefix_multiple(ET.CHANNEL,2)).values()) for d in shared_demands]
                variables_to_keep = [item for l in variables_to_keep for item in l]

                vars_to_remove = list(set(rsa2.base.bdd.vars) - set(variables_to_keep))
                f = rsa2.expr.exist(*vars_to_remove)

                needed = [var2 for var2 in rsa2.base.bdd.vars if var2 not in rsa1.base.bdd.vars]
                rsa1.base.bdd.declare(*[var for var in needed if prefixes[ET.CHANNEL] in var])

                rsa1.expr = rsa1.expr & rsa2.base.bdd.copy(f, rsa1.base.bdd)
                if rsa1.expr == rsa1.base.bdd.false:
                    self.validSolutions = False
                    return
                        
        self.solutions = rsa_list

    def get_size(self):
        return sum(map(lambda x: len(x.base.bdd),self.solutions))

    def get_solution(self):
        def get_assignments(bdd:_BDD, expr):
            return list(bdd.pick_iter(expr))
        
        combined_assignments = {}
        demand_to_l_assignment = {}
        for i,rsa in enumerate(self.solutions):
            rsa.expr = rsa.base.bdd.copy(rsa.expr, self.base.bdd)
            demands_in_current_rsa = self.rsa_to_demands[rsa]
            
            #Find the l assignments, that we need to '&' with, based on what demands the current rwa have
            current_l_assignemnts_to_adher_to = self.base.bdd.true
            for d in demands_in_current_rsa: 
                if d in demand_to_l_assignment: 
                    current_l_assignemnts_to_adher_to = current_l_assignemnts_to_adher_to & demand_to_l_assignment[d]#Maybe wrong later :)
            
            #'&' together with the previous rwa
            onlyValidSolutionsFromCurrentrwa = rsa.expr & current_l_assignemnts_to_adher_to

            #Get a random assignment from the current rsa   
            if i == 0: 
                current_assignment = get_assignments(self.base.bdd, onlyValidSolutionsFromCurrentrwa)[3] #Maybe incorrect Base
            else: 
                current_assignment = get_assignments(self.base.bdd, onlyValidSolutionsFromCurrentrwa)[0] #Maybe incorrect Base

            #Update the demand_to_l_assignemnt dict, based on the new current assignment
            for d in demands_in_current_rsa: 
                if d not in demand_to_l_assignment.keys():
                    expr = self.base.bdd.true
                    #Find the specific wavelengths assignements for d
                    #Create the expression ^ it togethere
                    for variable,trueOrFalse in current_assignment.items(): 
                        if 'l' in variable and variable.endswith(f"_{d}"):
                            k = self.base.bdd.var(variable)
                            if trueOrFalse == True: 
                                expr = expr & k
                            else: 
                                expr = expr & ~k
                    demand_to_l_assignment[d] = expr
            #Add the assignment, to the combined_assignemnts
            combined_assignments.update(current_assignment)

        return combined_assignments

    def count(self):
        return 1 if self.validSolutions else 0

class SplitAddAllBlock():
    def __init__(self, G, rsa_list:list, demands:dict[int,Demand], graphToDemands):
        self.base = SplitBDD(G, demands, rsa_list[0].base.ordering,  rsa_list[0].base.channel_data, rsa_list[0].base.reordering)

        self.expr = self.base.bdd.true
        self.G = G
        self.demands = demands
        self.graphToDemands = graphToDemands

        #Combine all of the solutions togethere to a single solution
        print("readyToAdd")
        for rsa in rsa_list:
            self.expr = self.expr & rsa.base.bdd.copy(rsa.expr, self.base.bdd)

        print("workds")
        # if encoded_path: 
        #     numberOfVarsNeedToEncodePaths = math.log2(len(paths))
        #     for rsa in rsa_list:
        #         varsUsedToEncodePaths = graph_to_new_paths[]

class ModulationBlock():
    def __init__(self, base: BaseBDD, modulation: Callable):
        self.expr = base.bdd.false
        for path in base.paths:
            path_expr = base.encode(ET.PATH, base.get_index(path, ET.PATH))
            or_expr = base.bdd.false
            for d in base.demand_vars:
                for c in base.demand_to_channels[d]:
                   if len(c) == modulation(path) * base.demand_vars[d].size:
                        or_expr |= base.encode(ET.CHANNEL, base.get_index(c, ET.CHANNEL))

            self.expr |= path_expr & or_expr         
                    
class RoutingAndChannelBlock():
    def __init__(self, demandPath : DemandPathBlock, modulation: ModulationBlock, base: BaseBDD, limit=False):

        d_list = base.get_encoding_var_list(ET.DEMAND)
        c_list = base.get_encoding_var_list(ET.CHANNEL)
        
        self.expr = base.bdd.true


        for i in base.demand_vars.keys():
                        
            channel_expr = base.bdd.false
            for channel in base.demand_to_channels[i]:
                index = base.get_index(channel, ET.CHANNEL)
                channel_expr |= base.encode(ET.CHANNEL, index)
            
            channel_subst = base.bdd.let(base.get_channel_vector(i),channel_expr)
        
            demandPath_subst = base.bdd.let(base.get_p_vector(i),demandPath.expr)
            subst = {}
            subst.update(base.get_p_vector(i))
            subst.update(base.get_channel_vector(i))
            modulation_subst = base.bdd.let(subst,modulation.expr)
            self.expr = (self.expr &  (demandPath_subst & channel_subst & modulation_subst & base.encode(ET.DEMAND, i)).exist(*(d_list+c_list)))
    
class ChannelFullNoClashBlock():
    def __init__(self,  rwa: Function, noClash, base: BaseBDD):
        self.expr = rwa
        self.base = base

        d_list = base.get_encoding_var_list(ET.DEMAND)
        dd_list = base.get_encoding_var_list(ET.DEMAND, base.get_prefix_multiple(ET.DEMAND, 2))
        pp_list = base.get_encoding_var_list(ET.PATH, base.get_prefix_multiple(ET.PATH, 2))
        cc_list = base.get_encoding_var_list(ET.CHANNEL, base.get_prefix_multiple(ET.CHANNEL, 2))
        
        d_expr = []

        for i in base.demand_vars.keys():
            noClash_subst = base.bdd.true

            for j in base.demand_vars.keys():
                if i < j:
                    continue
        
                subst = {}
                subst.update(base.get_p_vector(i))
                subst.update(base.make_subst_mapping(pp_list, list(base.get_p_vector(j).values())))

                subst.update(base.get_channel_vector(i))
                subst.update(base.make_subst_mapping(cc_list, list(base.get_channel_vector(j).values())))
                noClash_subst = base.bdd.let(subst, noClash.expr) & base.encode(ET.DEMAND, i) & base.bdd.let(base.make_subst_mapping(d_list, dd_list), base.encode(ET.DEMAND, j)) 
                d_expr.append(noClash_subst.exist(*(d_list + dd_list)))
        
        i_l = 0
        
        for j in range(i_l, len(d_expr)):
            
            # print(f"{j}/{len(d_expr)}")
            d_e = d_expr[j] 
            self.expr = self.expr & d_e

class ChannelSequentialBlock():
    def __init__(self, base: BaseBDD):
        self.expr = base.bdd.true
        demand_channel_substs = {d: base.get_channel_vector(d) for d in base.demand_vars}
        
        for i, d_i in enumerate(base.demand_vars.keys()):
            channels = base.demand_to_channels[d_i]
            d_expr = base.bdd.false

            for channel in channels:
                if channel[0] == 0:
                    ci = base.get_index(channel, ET.CHANNEL)
                    d_expr |= base.bdd.let(demand_channel_substs[d_i], base.encode(ET.CHANNEL, ci))
                
                else:
                    for j, d_j in enumerate(base.demand_vars.keys()):
                        if j >= i:
                            break
                        ci = base.get_index(channel, ET.CHANNEL)
                        
                        connected = base.connected_channels[base.get_index(channel, ET.CHANNEL)]
                        for c in connected:
                            cj = base.get_index(base.unique_channels[c], ET.CHANNEL)
                            d_expr |= (base.bdd.let(demand_channel_substs[d_i], base.encode(ET.CHANNEL, ci)) & base.bdd.let(demand_channel_substs[d_j], base.encode(ET.CHANNEL, cj)))
            

            self.expr &= d_expr
            print(self.expr.count())

        # for i, channel in enumerate(base.unique_channels):
        #     # All channels starting in slot 0 are valid. 
        #     if channel[0] == 0:
        #         continue
            
        #     if_this = base.bdd.false
        #     then_that = base.bdd.false
            
        #     for d in base.demand_vars:
                
        #         # only necessary to add constraint for channel if demand can use the channel
        #         if channel in base.demand_to_channels[d]:
        #             if_this |= base.bdd.let(demand_channel_substs[d], base.encode(ET.CHANNEL, i))
                    
        #         for j in base.connected_channels[i]:
        #             if base.unique_channels[j] in base.demand_to_channels[d]:
        #                 then_that |= base.bdd.let(demand_channel_substs[d], base.encode(ET.CHANNEL, j))
                    
class PathEdgeOverlapBlock(): 
    def __init__(self, base: BaseBDD):
        self.expr = base.bdd.false

        for i,p in enumerate(base.paths):
            for e in p: 
                edge = base.encode(ET.EDGE, base.get_index(e, ET.EDGE))
                path = base.encode(ET.PATH, base.get_index(p, ET.PATH))
                self.expr |= (path & edge)

class FailoverBlock():
    def __init__(self, base: BaseBDD, rsa_solution, path_edge_overlap: PathEdgeOverlapBlock):
        self.base = base
        big_e_expr = base.bdd.false
        for e in base.edge_vars: 
            demandPathEdgeoverlap = base.bdd.true

            for i in base.demand_vars.keys():
                demandPath_subst = base.bdd.let(base.get_p_vector(i), path_edge_overlap.expr)
                demandPathEdgeoverlap &= (~demandPath_subst)
            
            big_e_expr |= (demandPathEdgeoverlap & base.encode(ET.EDGE, base.get_index(e, ET.EDGE)))

        self.expr = rsa_solution.expr & big_e_expr


if __name__ == "__main__":
    pass
