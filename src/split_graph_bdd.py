from enum import Enum
import time

has_cudd = False

try:
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
    
    
class SplitBDD(BDD):
    
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
        self.node_vars = {v:i for i,v in enumerate(topology.nodes)}
        self.edge_vars = {e:i for i,e in enumerate(topology.edges)} 
        self.demand_vars = {(i):d for i,d in enumerate(demands.values())}
        self.encoded_node_vars :list[str]= []
        self.encoded_source_vars :list[str]= []
        self.encoded_target_vars :list[str]= []
        self.wavelengths = wavelengths
        self.binary = binary
        self.encoding_counts = {
            BDD.ET.NODE: math.ceil(math.log2(len(self.node_vars))) if binary else len(self.node_vars),
            BDD.ET.EDGE:  math.ceil(math.log2(len(self.edge_vars))) if binary else len(self.edge_vars),
            BDD.ET.DEMAND:  math.ceil(math.log2(max(max(max([i for i, d in self.demand_vars.items()]), len(self.demand_vars)), 2))),
            BDD.ET.PATH:  len(self.edge_vars),
            BDD.ET.LAMBDA: max(1, math.ceil(math.log2(wavelengths))) if binary else wavelengths,
            BDD.ET.SOURCE: math.ceil(math.log2(len(self.node_vars))) if binary else len(self.node_vars),
            BDD.ET.TARGET: math.ceil(math.log2(len(self.node_vars))) if binary else len(self.node_vars)
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

class SplitRWAProblem:
    def __init__(self, G: MultiDiGraph, demands: dict[int, Demand], ordering: list[BDD.ET], wavelengths: int, group_by_edge_order = False, interleave_lambda_binary_vars=False, generics_first = False, with_sequence = False, wavelength_constrained=False, binary=True, reordering=False, only_optimal=False):
        s = time.perf_counter()
        self.base = SplitBDD(G, demands, ordering, wavelengths, group_by_edge_order, interleave_lambda_binary_vars, generics_first, binary, reordering)

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
 


class AddBlock3():
    def __init__(self, G, subgraphs, rwa_list:list[SplitRWAProblem], oldDemands:dict[int,Demand], newDemands:dict[int,Demand], graphToNewDemands, oldDemandsToNewDemands:dict[int,list[int]]):
        self.base = SplitBDD(G, newDemands, rwa_list[0].base.ordering,  rwa_list[0].base.wavelengths, 
                            rwa_list[0].base.group_by_edge_order, rwa_list[0].base.interleave_lambda_binary_vars,
                            rwa_list[0].base.generics_first, True, rwa_list[0].base.reordering)
        res = self.base.bdd.true
        #Rename each subgraph, to unique demands and wavelengths. 
        itera = -1
        for iii,g in enumerate(subgraphs): 
            if g not in graphToNewDemands : 
                continue
            itera+= 1
            renameDict = {}
            # print("subgraph: ", iii, g)     #Pritn all of the nodes and edges
            #                                 #Test if solution is correct. 
            # print("subgraph: ", iii, g.edges(data="id")) 
            
            #Generate dicts from demands to unique demandsIds
            demand_in_g_to_unique_demand:dict[int,int] = {}
            for i, d in enumerate(graphToNewDemands[g]):
                demand_in_g_to_unique_demand.update({i:d})

            #create the dictionary with rename values in it
            for demand_in_g_2, renamed_demand in demand_in_g_to_unique_demand.items():
                #Create the l rename mapping. We go from the old l demands to new l demadns 
                for k in range(1,rwa_list[itera].base.encoding_counts[BDD.ET.LAMBDA]+1): #Fuck det virker ikke, da der kun er få rwa_list men mange andre ting 
                    current_l = "l"+str(k)+"_"+str(demand_in_g_2)   #skal ll variabler også ændres?
                    renamed_l = "l"+str(k)+"_"+str(renamed_demand)
                   
                    current_ll = "ll"+str(k)+"_"+str(demand_in_g_2)   #skal ll variabler også ændres?
                    renamed_ll = "ll"+str(k)+"_"+str(renamed_demand)
                    renameDict.update({current_l:renamed_l, current_ll:renamed_ll})
                    
                #Create the p renaming mapping. Go from old p to new p variables. 
                for i,e in enumerate(subgraphs[iii].edges):
                    current_p = f"p{i}_{demand_in_g_2}"
                    renamed_p = f"p{i}_{renamed_demand}"
                    renameDict.update({current_p:renamed_p})

            #declare new variables and relabel old variables to new ones, also declare in base
            rwa_list[itera].base.bdd.declare(*renameDict.values())
            rwa_list[itera].rwa = rwa_list[itera].base.bdd.let(renameDict,rwa_list[itera].rwa)
            self.base.bdd.declare(*renameDict.values())


        #Combine all of the solutions togethere to a single solution
        for rwa in rwa_list:
            res = res & rwa.base.bdd.copy(rwa.rwa, self.base.bdd)
        

        #Force demands to have same wavelength
        for old_demand, list_of_new_demands in oldDemandsToNewDemands.items():
            if len(list_of_new_demands) > 1: 
                vard_list = []
                for d in list_of_new_demands: 
                    vard_list.append(self.base.get_lam_vector(d))

                for i, k in enumerate(vard_list):
                    
                    if i+1 >= len(vard_list):
                        break
                    res = res & self.base.equals(list(vard_list[i].values()), list(vard_list[i+1].values()))
            else:
                pass#add this case
            
        

        
        #Rename from the unique demands, to old demands
        renameDict:dict[str,str] = {}
        for g in subgraphs: 
            if g not in graphToNewDemands: 
                continue
            g_demand_to_old_demand:dict[int,int] ={} 
            demand_in_g:list[int] = graphToNewDemands[g] #May be an demand instead

            for oldDemand, listOfNewDemands in oldDemandsToNewDemands.items():
                for demand in demand_in_g:
                    if demand in listOfNewDemands:
                        g_demand_to_old_demand.update({demand:oldDemand})

            
            g_edge_to_global_edge:dict[int,int] = {}
            for i,e in enumerate(g.edges):
                g_edge_to_global_edge.update({i:G.edges[e]["id"]})
            for new_d in demand_in_g:
                for i,e in enumerate(g.edges):
                    current_p = "p"
                    renamed_p = "p"
                    renamed_p += str(g_edge_to_global_edge[i])+"_"  
                    current_p += str(i)+"_"  
                    renamed_p += str(g_demand_to_old_demand[new_d])  
                    current_p += str(new_d) 
                    renameDict.update({current_p:renamed_p})
        res = self.base.bdd.let(renameDict, res)
        wavelengthsRenameDict:dict[str,str] = {}

        for old_demand, list_of_new_demands in oldDemandsToNewDemands.items():
            vard_list = []
            for d in list_of_new_demands: 
                vard_list.append(self.base.get_lam_vector(d))
            
            for lists in vard_list:
                for single in lists.values():

                    kkk = single[0:3]+str(old_demand)
                    wavelengthsRenameDict[single] = kkk

        res = self.base.bdd.let(wavelengthsRenameDict, res)
        self.expr = res

        def find_edges_not_in_subgraphs(graph, subgraphs):
            # Create a set to store edges present in subgraphs
            subgraph_edges = set()
            for subgraph in subgraphs:
                subgraph_edges.update(subgraph.edges(data="id"))
            # Create a set to store edges present in the original graph but not in any subgraph
            edges_not_in_subgraphs = set(graph.edges(data="id")) - subgraph_edges

            return edges_not_in_subgraphs

        #Set Edges not used to False
        for d in oldDemands: 
            currentNewDemands = oldDemandsToNewDemands[d]
            graphsUsed = {}
            #Find all subgraphs used
            for g in subgraphs: 
                for dd in currentNewDemands:
                    if g in graphToNewDemands: 
                        if dd in graphToNewDemands[g]: 
                            graphsUsed[g] = dd       
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

                self.expr = self.expr & ~ v





if __name__ == "__main__":
    import topology

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
    print("h\n\n")
    for g in subgraphs:
        print(g.nodes(data="id"))
        print(g.edges(data="id"))
        print("\n,")

    # oldDemands = {0: Demand("A", "B"), 1:Demand("A","D"), 2:Demand("A", "E"),3:Demand("A","B"), 4:Demand("E", "A") }
    numOfDemands =4
    oldDemands = {0:Demand("A","B")}
    oldDemands = topology.get_demands(G, numOfDemands, seed=2)
    print("demands", oldDemands)


    newDemandsDict , oldDemandsToNewDemands, graphToNewDemands = topology.split_demands(G, subgraphs, removedNode, oldDemands)
    print("newDemadns", newDemandsDict)
    print(" oldToNewDemands", oldDemandsToNewDemands)
    print("GraptToDemands", graphToNewDemands)
    
    types = [BDD.ET.EDGE, BDD.ET.LAMBDA, BDD.ET.NODE, BDD.ET.DEMAND, BDD.ET.TARGET, BDD.ET.PATH, BDD.ET.SOURCE]
    

    solutions = []  
    wavelengths =6
    print("Solve")
    for g in subgraphs: 

        if g in graphToNewDemands:
            demIndex = graphToNewDemands[g]
            res:dict[int,Demand] = {}
            for d in demIndex:
                res[d] = newDemandsDict[d]

            rw1 = SplitRWAProblem(g, res, types, wavelengths, group_by_edge_order =True, generics_first=False)


            solutions.append(rw1)
        else: 
            pass

    print("ready to add")
    add=AddBlock3(G, subgraphs, solutions, oldDemands, newDemandsDict, graphToNewDemands, oldDemandsToNewDemands)
    print("done")

    base = BDD(G,oldDemands,types,wavelengths,group_by_edge_order=True,generics_first=False).bdd
    rw2 = RWAProblem(G, oldDemands, types, wavelengths, group_by_edge_order =True, generics_first=False)

    f1 = rw2.base.bdd.copy(rw2.rwa, base)
    f2 = add.base.bdd.copy(add.expr, base)
    
    # print([x for x in rw2.base.bdd.vars.keys() if x not in add.base.bdd.vars.keys()])
    # print(add.base.bdd.vars.keys(), len(add.base.bdd.vars.keys()))
    # print(rw2.base.bdd.vars.keys(), len(add.base.bdd.vars.keys()))

    ass_our = get_assignments(add.base.bdd, add.expr)
    ass_base = get_assignments(rw2.base.bdd, rw2.rwa)

    print(len(ass_our), len(ass_base))    

    print("nice",f2 == f1)

    def get_assignments(bdd:_BDD, expr):
        return list(bdd.pick_iter(expr))

    print("Vi gør kar til at printe :P")
    from draw_general import draw_assignment
    import time
    for i in range(1,10000): 
        assignments = get_assignments(add.base.bdd, add.expr)
        if len(assignments) < i:
            break
        
        draw_assignment(assignments[i-1], add.base, G)
        user_input = input("Enter something: ")    