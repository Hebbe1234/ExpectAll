import time
from typing import Callable

from niceBDD import BaseBDD, ET, DynamicVarsBDD, prefixes
from itertools import combinations

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
from demands import Demand
import random 
random.seed(10)

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
        


class DynamicVarsChannelSequentialBlock():
    def __init__(self, base: DynamicVarsBDD):
        print("SEQ initiating...")
        self.expr = base.bdd.true
        
        for d_i in base.demand_vars.keys():
            channels = base.demand_to_channels[d_i]
            d_expr = base.bdd.false

            for channel in channels:
                if channel[0] == 0:
                    ci = base.get_index(channel, ET.CHANNEL, d_i)
                    d_expr |= base.encode(ET.CHANNEL, ci, d_i)
                
                else:
                    for d_j in base.potential_overlap_graph.neighbors(d_i):
                        
                        
                        ci = base.get_index(channel, ET.CHANNEL, d_i)
                        
                        connected = base.connected_channels[base.get_global_index(channel, ET.CHANNEL)]
                        
                        for c in connected:
                            selected_channel = base.unique_channels[c]
                            if selected_channel in base.demand_to_channels[d_j]:
                                cj = base.get_index(base.unique_channels[c], ET.CHANNEL, d_j)
                                d_expr |= base.encode(ET.CHANNEL, ci, d_i) & base.encode(ET.CHANNEL, cj, d_j)
            

            self.expr &= d_expr
        print("Gaps gone")


class PathEdgeOverlapBlock(): 
    def __init__(self, base: BaseBDD):
        self.expr = base.bdd.false
        for d in base.demand_vars:
            for i,p in enumerate(base.d_to_paths[d]):
                for e in base.paths[p]: 
                    edge = base.encode(ET.EDGE, base.get_index(e, ET.EDGE,0))
                    path = base.encode(ET.PATH, i, d)
                    self.expr |= (path & edge)




class UsageBlock():
    def __init__(self, base, rsa_solution, num_slots: int, start_index = 0, is_function =  False):
        self.base = base
        self.expr = rsa_solution.expr if not is_function else rsa_solution
        
        relevant_channels = [c for c in base.channel_data.unique_channels if c[-1] < start_index + num_slots]
        
        for d in base.demand_vars:
            d_expr = base.bdd.false
            for c in relevant_channels:
                if c not in base.demand_to_channels[d]:
                    continue
                
                if len(c) in [m * base.demand_vars[d].size for m in base.demand_vars[d].modulations]:               
                    d_expr |= base.encode(ET.CHANNEL, base.get_index(c, ET.CHANNEL, d), d)

            self.expr &= d_expr


class EdgeFailoverNEvaluationBlock(): 
    def get_combinations(self, nums, k):
        all_combinations = combinations(nums, k)
        unique_combinations = {tuple(sorted(comb)) for comb in all_combinations}
        return [list(comb) for comb in unique_combinations]
        

    def __init__(self, base: BaseBDD, rsa_solution, failure : int, usingDynymicVars = False):
        self.base = base
        self.rsa_solution = rsa_solution
        self.edge_to_failover = {}
        combinations = self.get_combinations(self.base.topology.edges(keys=True), failure)
        for comb in combinations:
            k = self.rsa_solution.expr
            entry = tuple()
            for e in comb: 
                entry += (e,)
                if usingDynymicVars : 
                    k = self.calculate_1_more_edge_failover_dynamic_vars(k, e)
                else : 
                    k = self.calculate_1_more_edge_failover(k, e)
            self.edge_to_failover[entry] = (self.base.bdd.false != k)

            
    def calculate_1_more_edge_failover(self, current_expr, edge):
        paths_that_uses_the_edge = []
        for i, p in enumerate(self.base.paths): 
            if edge in p: 
                paths_that_uses_the_edge.append(p)
        for d in self.base.demand_vars.keys():
            d_expr = self.base.bdd.true
            for p in paths_that_uses_the_edge:
                d_expr &= (~self.base.encode(ET.PATH, self.base.get_index(p, ET.PATH, d), d))

            current_expr &= d_expr 
        return current_expr
    
    def calculate_1_more_edge_failover_dynamic_vars(self, current_expr, edge):
        paths_that_uses_the_edge = []
        for i,p in enumerate(self.base.paths): 
            if edge in p: 
                paths_that_uses_the_edge.append(i)
        for d in self.base.demand_vars.keys():
            d_expr = self.base.bdd.true
            for p in self.base.d_to_paths[d]:
                path = self.base.paths[p]
                if edge not in path:
                    continue
                d_expr &= (~self.base.encode(ET.PATH, self.base.get_index(p, ET.PATH, d), d))

            current_expr &= d_expr 
        return current_expr

class DynamicVarsAssignment():
    def __init__(self, seq, modulation: Callable, base: DynamicVarsBDD):
        self.expr = base.bdd.true
        assignments_expr = base.bdd.true

        for d in base.demand_vars.keys():
            
            path_channel_expr = base.bdd.false
            for ip, path in enumerate(base.d_to_paths[d]):
                path_expr = base.encode(ET.PATH, ip, d)
                channel_expr = base.bdd.false

                for ic, channel in enumerate(base.demand_to_channels[d]):
                    if len(channel) == modulation(base.paths[path]) * base.demand_vars[d].size:
                        channel_expr |= base.encode(ET.CHANNEL, ic, d)
                
                path_channel_expr |= path_expr & channel_expr
                
                
            assignments_expr &= path_channel_expr

        self.expr = assignments_expr & seq  

class DynamicVarsNoClashBlock():
    def __init__(self, assignments: DynamicVarsAssignment, modulation: Callable, base: DynamicVarsBDD):
        self.expr = assignments.expr
        self.base = base
        no_clash_exprs = []
        
        for d1 in base.demand_vars.keys():
            for d2 in base.demand_vars.keys():
                if d1 <= d2:
                    continue
                
                big_overlap_expr = base.bdd.true
                
                for ip, path1 in enumerate(base.d_to_paths[d1]):
                    for jp, path2 in enumerate(base.d_to_paths[d2]):
                        if not (path1, path2) in base.overlapping_paths:
                            continue
                            
                        for ic, channel1 in enumerate(base.demand_to_channels[d1]):
                            if len(channel1) != modulation(base.paths[path1]) * base.demand_vars[d1].size:
                                continue
                            
                            for jc, channel2 in enumerate(base.demand_to_channels[d2]):
                                if len(channel2) != modulation(base.paths[path2]) * base.demand_vars[d2].size:
                                    continue
                                
                                if (channel1[0] >= channel2[0] and channel1[0] <= channel2[-1]) \
                                or (channel2[0] >= channel1[0] and channel2[0] <= channel1[-1]):
                                    big_overlap_expr &= (~(base.encode(ET.PATH, ip, d1) & base.encode(ET.PATH, jp, d2)) | ~(base.encode(ET.CHANNEL, ic, d1) & base.encode(ET.CHANNEL, jc, d2)))
                
                no_clash_exprs.append(big_overlap_expr)
        
        for no_clash in no_clash_exprs:
            self.expr &= no_clash




class SubSpectrumAddBlock():
    def __init__(self, rss, base):
        self.base = base
        self.expr = base.bdd.true
        news = []
        
        for rs in rss:
            needed = [var2 for var2 in rs.base.bdd.vars if var2 not in self.expr.bdd.vars]
            self.base.bdd.declare(*needed)
            news.append(rs.base.bdd.copy(rs.expr, self.base.bdd))   
        
        for n in news:
            self.expr &= n







class FailoverBlock2():
    def Get_all_edge_combinations(self, list_of_all_edges):
        from itertools import combinations
 
        def generate_sets(numbers, m):
            sets = []
            for i in range(m + 1):  # Include empty set
                sets.extend(combinations(numbers, i))
            return sets
 
        sets = generate_sets(list_of_all_edges, self.base.max_failovers)
        self.sets = sets
        all_possible_combinations = []
        for set1 in sets:
            current_edge_combination = []
            for e in set1:
                current_edge_combination.append(e)
            for _ in range(self.base.max_failovers-len(current_edge_combination)):
                current_edge_combination.append(-1)
 
            all_possible_combinations.append(current_edge_combination)
        self.all_combinations = all_possible_combinations
        return all_possible_combinations
    
 
    def __init__(self, base: DynamicVarsBDD, rsa_solution, path_edge_overlap: PathEdgeOverlapBlock):
        self.base = base
        print("about to combinatiosn")
        combinations = self.Get_all_edge_combinations(list(self.base.edge_vars.keys()))
 
        big_or_expression = base.bdd.false
 
        #Create a possible solution for each possible combination of edges that have failed.
        for edge_combination in combinations:
 
            edge_and_expr = base.bdd.true
 
            failover_count = 1

            #If an edge is unused, it gets encoded as [1,1,1,1,1,1,1,1]
            for edge in edge_combination:
                if edge == -1:
                    e_subst = 2**(base.encoding_counts[ET.EDGE])-1
                    unused_edge = base.encode(ET.EDGE, e_subst)
                    edge_and_expr &= base.bdd.let(base.get_e_vector(failover_count), unused_edge)
                    failover_count += 1
                    continue
                edge_encode = base.encode(ET.EDGE, base.get_index(edge, ET.EDGE,0))
                d = base.get_e_vector(failover_edge=failover_count)
                base.bdd.let(d, edge_encode)
                failover_count += 1
            
            #Ensure that no path overlaps between the edges.
            double_and_expr = base.bdd.true
            # for d in base.demand_vars.keys():
            #     for p_id_global in base.d_to_paths[d]:
            failover = 1
            for edge in edge_combination:
                if edge == -1:
                    failover += 1 #maybe not necessary, just to make the failover_encoding vectors match with the edge combinations
                    continue

                edge = base.get_index(edge, ET.EDGE,0)
                e_list = base.get_e_vector(failover)
                failover += 1

                e_subst = base.bdd.let(e_list,base.encode(ET.EDGE, edge))
                path_edge_overlap_subst = base.bdd.let(e_list,path_edge_overlap.expr)

                double_and_expr &= (e_subst  & ~path_edge_overlap_subst)
            
            big_or_expression |= (edge_and_expr & double_and_expr)
        self.expr = rsa_solution.expr & big_or_expression
 
 
 
class ReorderedGenericFailoverBlock():
    def __init__(self, base: DynamicVarsBDD, rsa_solution: FailoverBlock2):
        self.base = base
        self.expr = rsa_solution.expr
        self.all_solution_bdd = rsa_solution.expr
        bdd_vars = {}
        index = 0

        for failover in range(1,base.max_failovers+1):
            for item in range(1,base.encoding_counts[ET.EDGE]+1):
                bdd_vars[(f"{prefixes[ET.EDGE]}{item}_{failover}")] = index
                index += 1
 
        i = len(bdd_vars)
        rest = [v for v in base.bdd.vars if v not in bdd_vars]
        rest.sort(key=lambda x: base.bdd.var_levels[x]) #behold nuværende reordering for resterende variable

        for var in rest:
            bdd_vars[var] = i
            i += 1

        # gamle måde    
        # for var in base.bdd.vars:
        #     if var not in bdd_vars:
        #         bdd_vars[var] = i
        #         i += 1

        self.base.bdd.reorder(bdd_vars)
        print("reorder done?")

    def update_bdd_based_on_edge(self,e_list, expr_s=None):
        e_list = sorted(e_list)
        if len(e_list) > self.base.max_failovers:
            print("too many edges, failover only possible for",self.base.max_failovers, "edges")
            exit()

        self.base.bdd.configure(reordering=False)
        current_failover = 1

        expr = self.expr if expr_s==None else expr_s
        for failover,e in enumerate(e_list):
            e_encoding = self.base.encode(ET.EDGE, e)
            expr = expr & self.base.bdd.let(self.base.get_e_vector(failover+1),e_encoding)
            current_failover = failover+1+1

        # set remaining encodings of failover edges to 111111...
        for failover in range(current_failover, self.base.max_failovers+1):
            e_unused = 2**(self.base.encoding_counts[ET.EDGE])-1
            e_unused = self.base.encode(ET.EDGE, e_unused)
            expr &= self.base.bdd.let(self.base.get_e_vector(failover), e_unused)

        self.base.bdd.configure(reordering=True)
        return expr



class SlotBindingBlock():
    def __init__(self, base, rsa_solution: Function):
 
        self.base = base
        slot_vars = [f"s_{slot}" for slot in range(base.channel_data.input[1])]
        self.base.bdd.declare(*slot_vars)
        self.expr = rsa_solution
        
        all_d_expr = self.expr
        for d in self.base.demand_vars:
            d_expr = self.base.bdd.false
            for c in self.base.demand_to_channels[d]:
                c_expr = self.base.encode(ET.CHANNEL, base.get_index(c, ET.CHANNEL,d), d)
                for s in range(max(c)+1):
                    c_expr &= self.base.bdd.var(f"s_{s}")
                    
                d_expr |= c_expr

            all_d_expr &= d_expr
        
        print("Here")
        
                
        self.expr = all_d_expr

        print("Reordering")
        s=time.perf_counter()

        bdd_vars = {}
        
        for s in range(base.channel_data.input[1]):
            bdd_vars[f"s_{s}"] = s
                
        i = len(bdd_vars)
        rest = [v for v in self.base.bdd.vars if v not in bdd_vars]
        rest.sort(key=lambda x: self.base.bdd.var_levels[x]) #behold nuværende ordering for resterende variable

        for var in rest:
            bdd_vars[var] = i
            i += 1

        self.base.bdd.reorder(bdd_vars)
        print("reorder slot binding done")        
        print(time.perf_counter() - s)

if __name__ == "__main__":
    pass
