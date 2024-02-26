from enum import Enum
import time

from niceBDD import BaseBDD, ET, ChannelBDD, DynamicBDD, EncodedPathBDD, SplitBDD, prefixes

has_cudd = False

try:
    # raise ImportError()
    from dd.cudd import BDD as _BDD
    from dd.cudd import Function
    from dd.cudd import and_exists
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

class DemandPathBlock():
    def __init__(self, path, source : SourceBlock, target : TargetBlock, base):

        v_list = base.get_encoding_var_list(ET.NODE)
        s_list = base.get_encoding_var_list(ET.SOURCE)
        t_list = base.get_encoding_var_list(ET.TARGET)

        source_subst = base.bdd.let(base.make_subst_mapping(v_list, s_list), source.expr)
        target_subst = base.bdd.let(base.make_subst_mapping(v_list, t_list), target.expr)


        self.expr = (path.expr & source_subst & target_subst).exist(*s_list + t_list)  

class SingleWavelengthBlock():
    def __init__(self, base):
        self.expr = base.bdd.false
        for i in range(base.wavelengths):
            self.expr = self.expr | base.encode(ET.LAMBDA, i)

class NoClashBlock():
    def __init__(self, passes: PassesBlock, base):
        self.expr = base.bdd.false

        passes_1 = passes.expr
        mappingP = {}
        for e in list(base.edge_vars.values()):
            mappingP.update({f"{prefixes[ET.PATH]}{e}": f"{base.get_prefix_multiple(ET.PATH,2)}{e}"})
        
        passes_2: Function = passes.expr.let(**mappingP)
        
        l_list = base.get_encoding_var_list(ET.LAMBDA)
        ll_list =base.get_encoding_var_list(ET.LAMBDA, base.get_prefix_multiple(ET.LAMBDA, 2))
        
        d_list = base.get_encoding_var_list(ET.DEMAND)
        dd_list = base.get_encoding_var_list(ET.DEMAND, base.get_prefix_multiple(ET.DEMAND, 2))
        
        e_list = base.get_encoding_var_list(ET.EDGE)
        
        u = (passes_1 & passes_2).exist(*e_list)
        self.expr = u.implies(~base.equals(l_list, ll_list) | base.equals(d_list, dd_list))

class OverlapsBlock():
    def __init__(self, base: EncodedPathBDD):
        l_list = base.get_encoding_var_list(ET.LAMBDA)
        ll_list =base.get_encoding_var_list(ET.LAMBDA, base.get_prefix_multiple(ET.LAMBDA, 2))
        
        p_list = base.get_encoding_var_list(ET.PATH)
        pp_list = base.get_encoding_var_list(ET.PATH, base.get_prefix_multiple(ET.PATH, 2))
        
        self.expr = base.bdd.false
        
        for (i, j) in base.overlapping_paths:
            path1 = base.encode(ET.PATH, i)
            path2 = base.bdd.let(base.make_subst_mapping(p_list, pp_list), base.encode(ET.PATH, j))           
            self.expr |= (path1 & path2 & base.equals(l_list, ll_list))
 

class RoutingAndWavelengthBlock():
    def __init__(self, demandPath : DemandPathBlock, wavelength: SingleWavelengthBlock, base, constrained=False):

        d_list = base.get_encoding_var_list(ET.DEMAND)
        l_list = base.get_encoding_var_list(ET.LAMBDA)
        self.expr = base.bdd.true

        for i in base.demand_vars.keys():
            wavelength_subst = base.bdd.false
            
            if constrained:
                for w in range(min(base.wavelengths, i+1)):
                    wavelength_subst |= base.bdd.let(base.get_lam_vector(i),base.encode(ET.LAMBDA, w))
            else:
                wavelength_subst = base.bdd.let(base.get_lam_vector(i),wavelength.expr)

        
            demandPath_subst = base.bdd.let(base.get_p_vector(i),demandPath.expr)
            self.expr = (self.expr &  (demandPath_subst & wavelength_subst & base.encode(ET.DEMAND, i)).exist(*(d_list+l_list)))

# This has not been implemented in an efficient manner
class SimplifiedRoutingAndWavelengthBlock():
    def __init__(self, rwb: Function, base):
        ps = sum([list(base.get_p_vector(d).values()) for d in base.demand_vars.keys()],[])
        all_lambdas = rwb.exist(*ps)
        # remaining_lambdas = list(base.bdd.pick_iter(all_lambdas))
        
        remaining = all_lambdas

        
        assignment = base.bdd.pick(remaining)
        i = 0
        while assignment is not None and i < 100000:
            print(remaining.count())
            lambdas = self.identify_lambdas(assignment, base)
            transformations = self.transform(lambdas, base)
            remove_expr = base.bdd.false
            for t in transformations:
                newLambdas = {d: t[l] for d,l in lambdas.items()}
                d_expr = base.bdd.true
                for d,l in newLambdas.items():
                    d_expr &= base.bdd.let(base.get_lam_vector(int(d)),base.encode(ET.LAMBDA, l))
                
                remove_expr |= d_expr
            i += 1
            
            # expr = self.assignment_to_expr(assignment, base)
            
            remaining = remaining & ~(remove_expr)
            assignment = base.bdd.pick(remaining) 
            
        # while len(remaining_lambdas) != 0:
        #     pass
    def assignment_to_expr(self, assignment: dict[str, bool], base):
        expr = base.bdd.true
        for k,v in assignment.items():
            expr &= base.bdd.var(k) if v else ~base.bdd.var(k)
        
        return expr
    
    def identify_lambdas(self, assignment: dict[str, bool], base):
        def power(l_var: str):
            val = int(l_var.replace(prefixes[ET.LAMBDA], ""))
            return 2 ** (base.encoding_counts[ET.LAMBDA] - val)
        
        colors = {str(k):0 for k in base.demand_vars.keys()}

        for k, v in assignment.items():     
            if k[0] == prefixes[ET.LAMBDA] and v:
                [l_var, demand_id] = k.split("_")
                colors[demand_id] += power(l_var)

        return colors 
        
    def transform(self, assignment: dict[str, int], base):
        lambdas = set(list(assignment.values()))
        transformations = []
        perms = permutations(range(base.wavelengths), len(lambdas))
        for p in  permutations(range(base.wavelengths), len(lambdas)):
            transformations.append({k:p[i] for i, k in enumerate(lambdas)})

        return transformations



class SequenceWavelengthsBlock():
    def __init__(self, rwa_block: RoutingAndWavelengthBlock, base):
        self.expr = rwa_block.expr
        
        demand_lambda_substs = {d: base.get_lam_vector(d) for d in base.demand_vars}
        
        for l in range(1, base.wavelengths):
            u = base.bdd.false
            v = base.bdd.false
            for d in base.demand_vars:
                u |= base.bdd.let(demand_lambda_substs[d], base.encode(ET.LAMBDA, l))
                
                if d < l:
                    v |= base.bdd.let(demand_lambda_substs[d], base.encode(ET.LAMBDA, l-1))

            self.expr &= u.implies(v)
      
                
class FullNoClashBlock():
    def __init__(self,  rwa: Function, noClash : Function, base):
        self.expr = rwa
        self.base = base
        d_list = base.get_encoding_var_list(ET.DEMAND)
        dd_list = base.get_encoding_var_list(ET.DEMAND, base.get_prefix_multiple(ET.DEMAND, 2))
        pp_list = base.get_encoding_var_list(ET.PATH, base.get_prefix_multiple(ET.PATH, 2))
        ll_list = base.get_encoding_var_list(ET.LAMBDA, base.get_prefix_multiple(ET.LAMBDA, 2))
        
        d_expr = []

        for i in base.demand_vars.keys():
            noClash_subst = base.bdd.true

            for j in base.demand_vars.keys():
                if i <= j:
                    continue
        
                subst = {}
                subst.update(base.get_p_vector(i))
                subst.update(base.make_subst_mapping(pp_list, list(base.get_p_vector(j).values())))

                subst.update(base.get_lam_vector(i))
                subst.update(base.make_subst_mapping(ll_list, list(base.get_lam_vector(j).values())))
                noClash_subst = base.bdd.let(subst, noClash) & base.encode(ET.DEMAND, i) & base.bdd.let(base.make_subst_mapping(d_list, dd_list), base.encode(ET.DEMAND, j)) 
                d_expr.append(noClash_subst.exist(*(d_list + dd_list)))
        
        i_l = 0

        
        for j in range(i_l, len(d_expr)):
            d_e = d_expr[j] 
            self.expr = self.expr & d_e

class OnlyOptimalBlock(): 
    def __init__(self,  rwa: Function, base):
        l = 1        
        rww =  base.bdd.false
        while (rww == base.bdd.false and l <= base.wavelengths):
            outer_expr = base.bdd.true
            for d in base.demand_vars: 
                d_expr = base.bdd.false

                for w in range(min(l, base.wavelengths)):
                    d_expr |= base.bdd.let(base.get_lam_vector(d),base.encode(ET.LAMBDA, w))
                outer_expr &= d_expr

            rww = rwa & outer_expr
            l += 1

        self.expr = rww

      
class CliqueWavelengthsBlock():
    def __init__(self, rwa_block: RoutingAndWavelengthBlock, cliques, base):
        self.expr = rwa_block.expr
        demand_lambda_substs = {d: base.get_lam_vector(d) for d in base.demand_vars}
        
        max_wavelengths = {
            d:max([len(c) for c in cliques if d in c]) for d in base.demand_vars
        } 
             
        for d in base.demand_vars:
            d_expr = base.bdd.false
            
            for l in range(min(max_wavelengths[d], base.wavelengths)):
                d_expr |= base.bdd.let(demand_lambda_substs[d], base.encode(ET.LAMBDA, l))

            self.expr &= d_expr 


class DynamicFullNoClash():
    def __init__(self, demands1: dict[int,Demand], demands2: dict[int,Demand], noClash: NoClashBlock, base: DynamicBDD, init: Function):
        self.expr = init
        self.base = base

        d_list = base.get_encoding_var_list(ET.DEMAND)
        dd_list = base.get_encoding_var_list(ET.DEMAND, base.get_prefix_multiple(ET.DEMAND, 2))
        pp_list = base.get_encoding_var_list(ET.PATH, base.get_prefix_multiple(ET.PATH, 2))
        ll_list = base.get_encoding_var_list(ET.LAMBDA, base.get_prefix_multiple(ET.LAMBDA, 2))
        
        d_expr = []


        for i in demands1.keys():
            noClash_subst = base.bdd.true

            for j in demands2.keys():

                subst = {}
                subst.update(base.get_p_vector(i))
                subst.update(base.make_subst_mapping(pp_list, list(base.get_p_vector(j).values())))

                subst.update(base.get_lam_vector(i))
                subst.update(base.make_subst_mapping(ll_list, list(base.get_lam_vector(j).values())))
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
        if not base1.wavelengths == base2.wavelengths:
            raise ValueError("Wavelengths not equal")
        if  max([0] + list(base1.demand_vars.keys())) != (min(list(base2.demand_vars.keys()))-1):
            print(base1.demand_vars)
            print(base2.demand_vars)
            raise ValueError("Demands keys are not directly sequential")

        demands = {}
        demands.update(base1.demand_vars)
        demands.update(base2.demand_vars)

        self.base = DynamicBDD(base1.topology,demands, base1.ordering, base1.wavelengths, init_demand = min(list(base1.demand_vars.keys())))
        old_assignments = base1.bdd.copy(rwa1.expr, self.base.bdd)
        
        new_assignments = base2.bdd.copy(rwa2.expr, self.base.bdd)

        passes=PassesBlock(base1.topology,self.base)
        noclash=NoClashBlock(passes, self.base)

        dynamicNoClash = DynamicFullNoClash(base1.demand_vars, base2.demand_vars, noclash, self.base, old_assignments & new_assignments)

        self.expr = (dynamicNoClash.expr)
 
class SplitAddBlock():
    def __init__(self, G, rwa_list:list, demands:dict[int,Demand], graphToDemands):
        self.base = SplitBDD(G, demands, rwa_list[0].base.ordering,  rwa_list[0].base.wavelengths, rwa_list[0].base.reordering)
        self.expr = self
        
        rwa_to_demands = {}
        self.validSolutions = True
        #make dict from rwa_problem to demnads
        for (rwa, (_, graph_demands)) in zip(rwa_list, graphToDemands.items()):
            rwa_to_demands[rwa] = graph_demands.keys()
        
        self.rwa_to_demands = rwa_to_demands
        # 'and' all subproblems' wavelengths together based on demands they share
        for rwa1, demands1 in rwa_to_demands.items():
            for rwa2, demands2 in rwa_to_demands.items():
                if rwa1 == rwa2:
                    continue
                
                shared_demands = list(set(demands1).intersection(set(demands2)))
                if shared_demands == []:
                    continue
                
                #exist variables away they do not share and 'and' remaining expression
                variables_to_keep = [list(rwa1.base.get_lam_vector(d).values()) for d in shared_demands] + [list(rwa1.base.get_lam_vector(d,"ll").values()) for d in shared_demands]
                variables_to_keep = [item for l in variables_to_keep for item in l]

                vars_to_remove = list(set(rwa2.base.bdd.vars) - set(variables_to_keep))
                f = rwa2.expr.exist(*vars_to_remove)

                needed = [var2 for var2 in rwa2.base.bdd.vars if var2 not in rwa1.base.bdd.vars]
                rwa1.base.bdd.declare(*[var for var in needed if "l" in var])

                rwa1.expr = rwa1.expr & rwa2.base.bdd.copy(f, rwa1.base.bdd)
                if rwa1.expr == rwa1.base.bdd.false:
                    self.validSolutions = False
                    return
                        
        self.solutions = rwa_list

    def get_solution(self):
        def get_assignments(bdd:_BDD, expr):
            return list(bdd.pick_iter(expr))
        
        combined_assignments = {}
        demand_to_l_assignment = {}
        for i,rwa in enumerate(self.solutions):
            rwa.rwa = rwa.base.bdd.copy(rwa.rwa, self.base.bdd)
            demands_in_current_rwa = self.rwa_to_demands[rwa]
            
            #Find the l assignments, that we need to ^ with, based on what demands the current rwa have
            current_l_assignemnts_to_adher_to = self.base.bdd.true
            for d in demands_in_current_rwa: 
                if d in demand_to_l_assignment: 
                    print("jjjjjjj", demand_to_l_assignment)
                    print("weird")
                    current_l_assignemnts_to_adher_to = current_l_assignemnts_to_adher_to & demand_to_l_assignment[d]#Maybe wrong later :)
                    print("aferWeigthThgifnh")
            #And togethere with the previous rwa

            onlyValidSolutionsFromCurrentrwa = rwa.rwa & current_l_assignemnts_to_adher_to

            #Get a random assignment from the current rwa   
            if i == 0: 
                current_assignment = get_assignments(self.base.bdd, onlyValidSolutionsFromCurrentrwa)[3] #Maybe incorrect Base
            else: 
                current_assignment = get_assignments(self.base.bdd, onlyValidSolutionsFromCurrentrwa)[0] #Maybe incorrect Base

            # current_assignment = get_assignments(self.base.bdd, onlyValidSolutionsFromCurrentrwa)[0] #Maybe incorrect Base
            print(current_assignment)
            #Update the demand_to_l_assignemnt dict, based on the new current assignment
            for d in demands_in_current_rwa: 
                if d not in demand_to_l_assignment.keys():
                    print("expr")
                    expr = self.base.bdd.true
                    #Find the specific wavelengths assignements for d
                    #Create the expression ^ it togethere
                    for variable,trueOrFalse in current_assignment.items(): 
                        print(variable, trueOrFalse)
                        if 'l' in variable and variable.endswith(f"_{d}"):
                            k = self.base.bdd.var(variable)
                            if trueOrFalse == True: 
                                expr = expr & k
                            else: 
                                expr = expr & ~k
                    print("last prnt)")
                    demand_to_l_assignment[d] = expr
            #Add the assignment, to the combined_assignemnts
            print("About to update", current_assignment)
            combined_assignments.update(current_assignment)

        return combined_assignments

    def count(self):
        return 1 if self.validSolutions else 0

class SplitAddAllBlock():
    def __init__(self, G, rwa_list:list, demands:dict[int,Demand], graphToDemands):
        self.base = SplitBDD(G, demands, rwa_list[0].base.ordering,  rwa_list[0].base.wavelengths, rwa_list[0].base.reordering)

        self.expr = self.base.bdd.true
        self.G = G
        self.demands = demands
        self.graphToDemands = graphToDemands

        #Combine all of the solutions togethere to a single solution
        for rwa in rwa_list:
            self.expr = self.expr & rwa.base.bdd.copy(rwa.expr, self.base.bdd)


        def find_edges_not_in_subgraphs(graph, subgraphs):
            # Create a set to store edges present in subgraphs
            subgraph_edges = set()
            for subgraph in subgraphs:
                subgraph_edges.update(subgraph.edges(keys=True, data="id"))
            # Create a set to store edges present in the original graph but not in any subgraph
            edges_not_in_subgraphs = set(graph.edges(keys=True, data="id")) - subgraph_edges

            return edges_not_in_subgraphs

        #Set Edges not used to False
        edgesNotUsedbdd = self.base.bdd.true
        for d in demands: 
            graphsUsed = {}
            for gg, smallDemands in graphToDemands.items():
                for dd in smallDemands:
                    if d == dd: 
                        graphsUsed[gg] = dd
            graphsUsed = list(graphsUsed.keys())
            edgesNotUsed = find_edges_not_in_subgraphs(G, graphsUsed)

            for e in edgesNotUsed: 
                myId = -222
                
                for ee in G.edges(keys=True, data="id"):
                    if e == ee:
                        myId = ee[2]
                        break

                myStr = "p"+str(myId)+"_"+str(d)
                v = self.base.bdd.var(myStr)
                edgesNotUsedbdd = edgesNotUsedbdd &  ~v
        self.expr = self.expr & edgesNotUsedbdd



class ChannelOverlap():
    def __init__(self, base: ChannelBDD):
        self.expr = base.bdd.false

        c_list = base.get_encoding_var_list(ET.CHANNEL)
        cc_list = base.get_encoding_var_list(ET.CHANNEL, base.get_prefix_multiple(ET.CHANNEL, 2))

        for (c1, c2) in base.overlapping_channels:
            c1_var = base.encode(ET.CHANNEL, c1)
            c2_var = base.bdd.let(base.make_subst_mapping(c_list, cc_list), base.encode(ET.CHANNEL, c2))
            
            self.expr |= c1_var & c2_var
            
class ChannelNoClashBlock():
    def __init__(self, passes: PassesBlock, channelOverlap: ChannelOverlap, base: ChannelBDD):
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


class RoutingAndChannelBlock():
    def __init__(self, demandPath : DemandPathBlock, base: ChannelBDD, limit=False):

        d_list = base.get_encoding_var_list(ET.DEMAND)
        c_list = base.get_encoding_var_list(ET.CHANNEL)
        
        self.expr = base.bdd.true


        for i in base.demand_vars.keys():
            
            channel_subst = base.bdd.false
            
            if limit:
                max_index = sum([demand.size for j, demand in base.demand_vars.items() if i > j]) 
                legal_channels = [channel for channel in base.demand_to_channels[i] if channel[0] <= max_index]
                channel_expr = base.bdd.false
                
                for channel in legal_channels:
                    index = base.get_index(channel, ET.CHANNEL)
                    channel_expr |= base.encode(ET.CHANNEL, index)
                
                channel_subst = base.bdd.let(base.get_channel_vector(i),channel_expr)
                      
            else:
                channel_expr = base.bdd.false
                for channel in base.demand_to_channels[i]:
                    index = base.get_index(channel, ET.CHANNEL)
                    channel_expr |= base.encode(ET.CHANNEL, index)
                
                
                channel_subst = base.bdd.let(base.get_channel_vector(i),channel_expr)

        
            demandPath_subst = base.bdd.let(base.get_p_vector(i),demandPath.expr)
            self.expr = (self.expr &  (demandPath_subst & channel_subst & base.encode(ET.DEMAND, i)).exist(*(d_list+c_list)))
    
class ChannelFullNoClashBlock():
    def __init__(self,  rwa: Function, noClash : ChannelNoClashBlock, base: ChannelBDD):
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
    def __init__(self, base: ChannelBDD):
        self.expr = base.bdd.true
        demand_channel_substs = {d: base.get_channel_vector(d) for d in base.demand_vars}
        
        for i, channel in enumerate(base.unique_channels):
            # All channels starting in slot 0 are valid. 
            if channel[0] == 0:
                continue
            
            if_this = base.bdd.false
            then_that = base.bdd.false
            
            for d in base.demand_vars:
                
                # only necessary to add constraint for channel if demand can use the channel
                if channel in base.demand_to_channels[d]:
                    if_this |= base.bdd.let(demand_channel_substs[d], base.encode(ET.CHANNEL, i))
                    
                    for j in base.connected_channels[i]:
                        if base.unique_channels[j] in base.demand_to_channels[d]:
                            then_that |= base.bdd.let(demand_channel_substs[d], base.encode(ET.CHANNEL, j))
                    
            self.expr &= if_this.implies(then_that)
            