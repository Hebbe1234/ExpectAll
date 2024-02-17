from enum import Enum
import time

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

import networkx as nx
from networkx import digraph
from networkx import MultiDiGraph
import math
from demands import Demand
from itertools import permutations
from bdd import *


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
    
    
class SplitBDD2(BDD):
    def __init__(self, topology: MultiDiGraph, demands: dict[int, Demand], ordering: list[BDD.ET], 
                 wavelengths = 2, group_by_edge_order = True, interleave_lambda_binary_vars=True, 
                 generics_first = True, binary=True, reordering=False):
        self.bdd = _BDD()
        if has_cudd:
            print("Has cudd")
            self.bdd.configure(
                # number of bytes
                max_memory=50 * (2**30),
                reordering=reordering)
        else:
            self.bdd.configure(reordering=reordering)
        self.G=topology
        self.ordering=ordering
        self.group_by_edge_order=group_by_edge_order
        self.interleave_lambda_binary_vars=interleave_lambda_binary_vars
        self.generics_first = generics_first
        self.reordering=reordering
        self.variables = []
        self.node_vars = {n: nId[1] for n, nId in zip(topology.nodes, topology.nodes(data=("id")))} 
        self.edge_vars = {e: eId[2] for e, eId in zip(topology.edges, topology.edges(data=("id")))}
        self.demand_vars = demands
        self.encoded_node_vars :list[str]= []
        self.encoded_source_vars :list[str]= []
        self.encoded_target_vars :list[str]= []
        self.wavelengths = wavelengths
        self.binary = binary
        self.encoding_counts = {
            BDD.ET.NODE: math.ceil(math.log2(1+(max([i for n, i in self.node_vars.items()])))),
            BDD.ET.EDGE:  math.ceil(math.log2(1+(max([i for e, i in self.edge_vars.items()])))), 
            BDD.ET.DEMAND:  math.ceil(math.log2(max(max(max([i for i, d in self.demand_vars.items()]), len(self.demand_vars)), 2))),
            BDD.ET.PATH:   1+(max([i for e, i in self.edge_vars.items()])),
            BDD.ET.LAMBDA: max(1, math.ceil(math.log2(wavelengths))) if binary else wavelengths,
            BDD.ET.SOURCE: math.ceil(math.log2(1+(max([i for n, i in self.node_vars.items()])))),
            BDD.ET.TARGET: math.ceil(math.log2(1+(max([i for n, i in self.node_vars.items()])))),
        }
        self.gen_vars(ordering, group_by_edge_order, interleave_lambda_binary_vars, generics_first)
        
    def gen_vars(self, ordering: list[BDD.ET], group_by_edge_order = False,  interleave_lambda_binary_vars = False, generic_first = False):
        
        for type in ordering:
            if type == BDD.ET.DEMAND:
                    self.declare_variables(BDD.ET.DEMAND)
                    self.declare_variables(BDD.ET.DEMAND, 2)
            elif type == BDD.ET.PATH:
                    self.declare_generic_and_specific_variables(BDD.ET.PATH, list(self.edge_vars.values()), group_by_edge_order, generic_first)
            elif type == BDD.ET.LAMBDA:
                self.declare_generic_and_specific_variables(BDD.ET.LAMBDA,  list(range(1, 1 + self.encoding_counts[BDD.ET.LAMBDA])), interleave_lambda_binary_vars, generic_first)
            elif type == BDD.ET.EDGE:
                self.declare_variables(BDD.ET.EDGE)
                self.declare_variables(BDD.ET.EDGE, 2)
            
            elif type in [BDD.ET.NODE,BDD.ET.SOURCE,BDD.ET.TARGET]:
                self.declare_variables(type)
            else: 
                raise Exception(f"Error: the given type {type} did not match any BDD type.")

    def declare_variables(self, type: BDD.ET, prefix_count: int = 1):
        d_bdd_vars = [f"{self.get_prefix_multiple(type, prefix_count)}{self.encoding_counts[type] - i}" for i in range(0,self.encoding_counts[type])]
        self.bdd.declare(*d_bdd_vars)
        
        return d_bdd_vars

    def declare_generic_and_specific_variables(self, type: BDD.ET, l: list[int], group_by_edge_order=False, generic_first=False):
        bdd_vars = []

        def append(item, demand):
            bdd_vars.append(f"{BDD.prefixes[type]}{item}_{demand}")
            bdd_vars.append(f"{self.get_prefix_multiple(type,2)}{item}_{demand}")
        
        def gen_generics():
            for item in l:
                bdd_vars.append(f"{BDD.prefixes[type]}{item}")
                bdd_vars.append(f"{self.get_prefix_multiple(type,2)}{item}")
        
        if generic_first:
            gen_generics()
        
        if group_by_edge_order:
            for item in l:
                for demand in self.demand_vars.keys():
                    append(item, demand)
        else:
            for demand in self.demand_vars.keys():
                for item in l:
                    append(item, demand)
                
        if not generic_first:
            gen_generics()
        
        self.bdd.declare(*bdd_vars)


    def make_subst_mapping(self, l1: list[str], l2: list[str]):
        return {l1_e: l2_e for (l1_e, l2_e) in zip(l1, l2)}
    
    def get_p_var(self, edge: int, demand =  None, override = None):
        if override is None:
            return f"{BDD.prefixes[BDD.ET.PATH]}{edge}{f'_{demand}' if demand is not None else ''}"
        
        return f"{override}{edge}{f'_{demand}' if demand is not None else ''}"

    def get_p_vector(self, demand: int , override = None):
        l1 = []
        l2 = []
        for edge in  self.edge_vars.values():
            l1.append(self.get_p_var(edge, None, override))
            l2.append(self.get_p_var(edge, demand, override))

        return self.make_subst_mapping(l1, l2)
    
    def get_lam_var(self, wavelength: int, demand = None, override = None):
        if override is  None:
            return f"{BDD.prefixes[BDD.ET.LAMBDA]}{wavelength}{f'_{demand}' if demand is not None else ''}"
        
        return f"{override}{wavelength}{f'_{demand}' if demand is not None else ''}"
        
    def get_lam_vector(self, demand: int, override = None):
        l1 = []
        l2 = []
        for wavelength in  range(1,self.encoding_counts[BDD.ET.LAMBDA]+1):
            l1.append(self.get_lam_var(wavelength, None, override))
            l2.append(self.get_lam_var(wavelength, demand, override))

        return self.make_subst_mapping(l1, l2)

    def get_index(self, item, type: BDD.ET):
        if type == BDD.ET.NODE:
            return self.node_vars[item]

        if type == BDD.ET.EDGE:
            return self.edge_vars[item]

        if type == BDD.ET.DEMAND:
            assert isinstance(item, int)
            return item

        return 0
    
    
    def encode(self, type: BDD.ET, number: int):
        if self.binary:
            return self.binary_encode(type, number)
        else:
            return self.unary_encode(type, number + 1)
        
    def unary_encode(self, type: BDD.ET, number: int):
        encoding_count = self.encoding_counts[type]
        encoding_expr = self.bdd.true
        for j in range(encoding_count):
            v = self.bdd.var(f"{BDD.prefixes[type]}{j+1}")
            if number != j+1:
                v = ~v 

            encoding_expr = encoding_expr & v
        
        return encoding_expr

    def binary_encode(self, type: BDD.ET, number: int):
        encoding_count = self.encoding_counts[type]
        encoding_expr = self.bdd.true
        for j in range(encoding_count):
            v = self.bdd.var(f"{BDD.prefixes[type]}{j+1}")
            if not (number >> (j)) & 1:
                v = ~v

            encoding_expr = encoding_expr & v
          
        return encoding_expr
    

    def get_prefix_multiple(self, type: BDD.ET, multiple: int):
        return "".join([BDD.prefixes[type] for _ in range(multiple)])

    def get_encoding_var_list(self, type: BDD.ET, override_prefix = None):
        offset = 0
        if type == BDD.ET.PATH:
            offset = 1
            ls = []
            for e, i in self.edge_vars.items(): 
                ls.append(f"{BDD.prefixes[type] if override_prefix is None else override_prefix}{i+1 - offset}")
            return ls
        return [f"{BDD.prefixes[type] if override_prefix is None else override_prefix}{i+1 - offset}" for i in range(self.encoding_counts[type])]

    def equals(self, e1: list[str], e2: list[str]):
        assert len(e1) == len(e2)

        expr = self.bdd.true
        for (var1, var2) in zip(e1,e2):
            s = (self.bdd.var(var1) & self.bdd.var(var2)) |(~self.bdd.var(var1) & ~self.bdd.var(var2))
            expr = expr & s

        return expr


def myPrint(s, before, after, string):
    print(after-s, after-before, string, flush=True)

class SplitRWAProblem2:
    def __init__(self, G: MultiDiGraph, demands: dict[int, Demand], ordering: list[BDD.ET], wavelengths: int, group_by_edge_order = False, interleave_lambda_binary_vars=False, generics_first = False, with_sequence = False, wavelength_constrained=False, binary=True, reordering=False, only_optimal=False):
        s = time.perf_counter()
        self.base = SplitBDD2(G, demands, ordering, wavelengths, group_by_edge_order, interleave_lambda_binary_vars, generics_first, binary, reordering)
        in_expr = InBlock(G, self.base)
        out_expr = OutBlock(G, self.base)
        source = SourceBlock(self.base)
        target = TargetBlock( self.base)
        trivial_expr = TrivialBlock(G, self.base)
        passes = PassesBlock(G, self.base)
        singleOut = SingleOutBlock(out_expr, passes, self.base)
        changed = ChangedBlock(passes, self.base)
        print("Building path BDD...")
        before_path = time.perf_counter()
        path = PathBlock(trivial_expr, out_expr,in_expr, changed, singleOut, self.base)
        after_path = time.perf_counter()
        print(after_path - s,after_path - before_path, "Path built", flush=True)
        demandPath = DemandPathBlock(path, source, target, self.base)
        
        
        print(self.base.demand_vars)
        pretty_print(self.base.bdd, source.expr)
        pretty_print(self.base.bdd, target.expr)
        pretty_print(self.base.bdd, path.expr & self.base.bdd.var("t2") & self.base.bdd.var("s2") & self.base.bdd.var("s3"))
        print(":::")
        pretty_print(self.base.bdd, demandPath.expr)
        singleWavelength_expr = SingleWavelengthBlock(self.base)
        noClash_expr = NoClashBlock(passes, self.base) 
        
        before1 = time.perf_counter()
        rwa = RoutingAndWavelengthBlock(demandPath, singleWavelength_expr, self.base, constrained=wavelength_constrained)
        after1 = time.perf_counter()

        myPrint(s, before1, after1, "routingAndWavelengthBlock")

        e1 = time.perf_counter()
        print(e1 - s, e1-s, "Blocks",  flush=True)

        sequenceWavelengths = self.base.bdd.true
        if with_sequence:
            sequenceWavelengths = SequenceWavelengthsBlock(rwa, self.base)
        
        # simplified = SimplifiedRoutingAndWavelengthBlock(rwa.expr & sequenceWavelengths.expr, self.base)
        
        #print(rwa.expr.count())
        # print((rwa.expr & sequenceWavelengths.expr).count())
        #print((sequenceWavelengths.expr).count())
        
        e2 = time.perf_counter()
        print(e2 - s, e2-e1, "Sequence", flush=True)
        full = rwa.expr #& sequenceWavelengths.expr
        
        if with_sequence:
            full = full & sequenceWavelengths.expr
        

        
        e3 = time.perf_counter()
       # print(e3 - s, e3-e2, "Simplify",flush=True)

        fullNoClash = FullNoClashBlock(full, noClash_expr, self.base)
        self.rwa = fullNoClash.expr
        e4 = time.perf_counter()
        print(e4 - s, e4 - e3, "FullNoClash", flush=True)
        print("")

        if only_optimal:
            e5 = time.perf_counter() 
            only_optimal = OnlyOptimalBlock(self.rwa, self.base)
            self.rwa = only_optimal.expr
            e6 = time.perf_counter()
            print(e6 - s, e6 - e5, "OnlyOptimal", flush=True)

    def get_assignments(self, amount):
        assignments = []
        
        for a in self.base.bdd.pick_iter(self.rwa):
            
            if len(assignments) == amount:
                return assignments

            assignments.append(a)
        
        return assignments    
        
    
    def print_assignments(self, true_only=False, keep_false_prefix=""):
        pretty_print(self.base.bdd, self.rwa, true_only, keep_false_prefix=keep_false_prefix)



class AddBlock():
    def __init__(self, G, rwa_list:list[SplitRWAProblem2], demands:dict[int,Demand], graphToDemands):
        self.base = SplitBDD2(G, demands, rwa_list[0].base.ordering,  rwa_list[0].base.wavelengths, 
                           rwa_list[0].base.group_by_edge_order, rwa_list[0].base.interleave_lambda_binary_vars,
                           rwa_list[0].base.generics_first, True, rwa_list[0].base.reordering)
        self.expr = self.base.bdd.true

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

                f = rwa2.rwa.exist(*vars_to_remove)

                needed = [var2 for var2 in rwa2.base.bdd.vars if var2 not in rwa1.base.bdd.vars]
                rwa1.base.bdd.declare(*[var for var in needed if "l" in var])

                rwa1.rwa = rwa1.rwa & rwa2.base.bdd.copy(f, rwa1.base.bdd)
                if rwa1.rwa == rwa1.base.bdd.false:
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



class AddAllBlock():
    def __init__(self, G, rwa_list:list[SplitRWAProblem2], demands:dict[int,Demand], graphToDemands):
        self.base = SplitBDD2(G, demands, rwa_list[0].base.ordering,  rwa_list[0].base.wavelengths, 
                            rwa_list[0].base.group_by_edge_order, rwa_list[0].base.interleave_lambda_binary_vars,
                            rwa_list[0].base.generics_first, True, rwa_list[0].base.reordering)
        self.expr = self.base.bdd.true
        self.G = G
        self.demands = demands
        self.graphToDemands = graphToDemands

        #Combine all of the solutions togethere to a single solution
        for rwa in rwa_list:
            self.expr = self.expr & rwa.base.bdd.copy(rwa.rwa, self.base.bdd)


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
                
                for ee in G.edges(data="id"):
                    if e == ee:
                        myId = ee[2]
                        break

                myStr = "p"+str(myId)+"_"+str(d)
                v = self.base.bdd.var(myStr)
                edgesNotUsedbdd = edgesNotUsedbdd &  ~v
        self.expr = self.expr & edgesNotUsedbdd


if __name__ == "__main__":
    import topology
    print("start_main")
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/3NodeSPlitGraph.dot"))
    G = nx.MultiDiGraph(nx.nx_pydot.read_dot("../dot_examples/split5NodeExample.dot"))
    G = topology.get_nx_graph(topology.TOPZOO_PATH +  "/Ai3.gml")

    import topology
    if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")
    for i,n in enumerate(G.nodes):
        G.nodes[n]['id'] = i
    for i,e in enumerate(G.edges):
        G.edges[e]['id'] = i

    subgraphs, removedNode = topology.split_into_multiple_graphs(G)
    if subgraphs == None or removedNode == None: 
        print("UNABLE TO SPLIT IT ")
        exit()

    numOfDemands =1

    oldDemands = {0: Demand("A", "B"), 1:Demand("A","D"), 2:Demand("A","D") }
    oldDemands = {0:Demand("A","D"), 1:Demand("B","D"), 2: Demand("B","D")}
    oldDemands = topology.get_demands(G, numOfDemands, seed=3)
    print("demands", oldDemands)


    newDemandsDict , oldDemandsToNewDemands, graphToNewDemands = topology.split_demands(G, subgraphs, removedNode, oldDemands)
    graphToNewDemands = topology.split_demands2(G, subgraphs, removedNode, oldDemands)

    types = [BDD.ET.EDGE, BDD.ET.LAMBDA, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH, BDD.ET.SOURCE]
    start_time = time.time()
    solutions = []  
    wavelengths = 5
    
    print("Solve")
    for g in subgraphs: 
        if g in graphToNewDemands:
            demands = graphToNewDemands[g]
            rw1 = SplitRWAProblem2(g, demands, types, wavelengths, group_by_edge_order=True, generics_first=False)
            solutions.append(rw1)
        else: 
            pass
    baseLineSolve = time.time()
    print("ready to add")
    add=AddBlock(G, solutions, oldDemands, graphToNewDemands)
    print(add.expr.count())
    exit()
    # res = add.get_solution()
    print("Here is the result", res)
    from draw_general import draw_assignment

    for r in res: 

        draw_assignment(res, add.base, G)
        user_input = input("Enter something: ")    

    exit()
    print(add.solutions)
    print("done")
    addSolved = time.time()

    print("Time from start to baselineSolve:", baseLineSolve - start_time )
    print("Time from baselineSolve to addSolve:", addSolved - baseLineSolve )


    start_time = time.time()
    base = BDD(G,oldDemands,types,wavelengths,group_by_edge_order=True,generics_first=False).bdd
    rw2 = RWAProblem(G, oldDemands, types, wavelengths, group_by_edge_order =True, generics_first=False)
    end_time = time.time()
    print(end_time - start_time)

    f1 = rw2.base.bdd.copy(rw2.rwa, base)
    f2 = add.base.bdd.copy(add.expr, base)
    

    ass_our = get_assignments(add.base.bdd, add.expr)
    ass_base = get_assignments(rw2.base.bdd, rw2.rwa)

    print("nice",f2 == f1)

    # def get_assignments(bdd:_BDD, expr):
    #     return list(bdd.pick_iter(expr))

    # print("Vi gør kar til at printe :P")
    # from draw_general import draw_assignment
    # import time
    # for i in range(1,10000): 
    #     print("h")
    #     assignments = get_assignments(add.base.bdd, add.expr)
    #     if len(assignments) < i:
    #         break
        
    #     draw_assignment(assignments[i-1], add.base, G)
    #     user_input = input("Enter something: ")    

