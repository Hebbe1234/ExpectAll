from functools import reduce
import itertools
from pyeda.inter import *
import re
from graphviz import Source
import pydot
import networkx as nx
import os


def drawBDD(bdd, outputFileName, clean=True):
    def removeZeroNode(graphString):
        g = pydot.graph_from_dot_data(bdd.to_dot())[0]
        g.write_dot("./out/cleaning.dot")
        f = open("./out/cleaning.dot").read()
        label0Id = re.search(r"(n.*)\t.*\n\t\tlabel=0", f).group(1)
        f = re.sub(r".*{}.*\n.*\n.*\n[^n]*".format(label0Id), "", f)
        f = re.sub(r"\[label=[01],", "[", f)
        return f

    dotString = bdd.to_dot()
    if clean:
        dotString = removeZeroNode(dotString)

    gv = Source(dotString)
    gv.render("./out/" + outputFileName, format="svg")

G = nx.DiGraph(nx.nx_pydot.read_dot("./dot_examples/simple_net.dot"))

gv = Source(open("./dot_examples/simple_net.dot").read())
gv.render("./out/simple_net", format="svg")

# Helper functions
andl = lambda a,b: a & b
orl = lambda a,b: a | b

def get_edges(node, network):
    return list(network.in_edges(node)) + list(network.out_edges(node))

def isNodeInRoute(network, node, node_vars, edge_vars):
    edges = get_edges(node, network)
    node_edge_vars = [edge_vars[str(e[0]) + str(e[1])] for e in edges]
    in_clauses = []
    for e1,e2 in itertools.combinations(node_edge_vars,2):
        rest = [~r for r in node_edge_vars if r != e1 and r != e2]
        
        in_clauses.append(e1 & e2 & (reduce(andl, rest, rest[0]) if len(rest) > 0 else expr(True)))
    

    in_clause = node_vars[node] & (reduce(orl, in_clauses, in_clauses[0]) if len(in_clauses) > 0 else expr(True))

    not_in_clause = ~node_vars[node] & reduce(andl, [~v for v in node_edge_vars], ~node_edge_vars[0]) if len(node_edge_vars) > 0 else expr(True)

    return (lambda x: ( x & in_clause ) | (x & not_in_clause))


def flow(network, demand, demand_var, node_vars, edge_vars):
    source = demand[0]
    s_edge_vars = [edge_vars[str(e[0]) + str(e[1])] for e in get_edges(source, network)]
    s_clauses = []
    
    for e in s_edge_vars:
        rest = [~r for r in s_edge_vars if r != e]
        s_clauses.append(demand_var & e & (reduce(andl, rest,rest[0]) if len(rest) > 0 else expr(True)))
    s_clause = reduce(orl, s_clauses)
   
    destination = demand[1]
    d_edge_vars = [edge_vars[str(e[0]) + str(e[1])] for e in get_edges(destination, network)]
    d_clauses = []
    for e in d_edge_vars:
        rest = [~r for r in d_edge_vars if r != e]
        d_clauses.append(demand_var & e & (reduce(andl, rest,rest[0]) if len(rest) > 0 else expr(True)))
    d_clause = reduce(orl, d_clauses )

    return s_clause & d_clause

def demand(network, demand, demand_var, node_vars, edge_vars, flow_funcs):
    flow_clauses = []
    for n in node_vars:
        if n == demand[0] or n == demand[1]:
            continue
        
        flow_clauses.append(flow_funcs[n](demand_var))

    flow_clauses.append(flow(network, demand, demand_var, node_vars, edge_vars))
    return reduce(andl, flow_clauses, flow_clauses[0])

def demand_unique(demand_vars):
    d_clauses = []
    for i,d in demand_vars.items():
        rest = [~r for i,r in demand_vars.items() if d != r]
        d_clauses.append(d & reduce(andl, rest, rest[0]) if len(rest) > 0 else expr(True))
    return reduce(orl, d_clauses, d_clauses[0])

def generateBDD(network: nx.DiGraph, demands):
    if len(demands) == 0:
        print("YOU MUST DEFINE AT LEAST ONE DEMAND")
        return
    
    demandVars = {i: bddvar("d_" + str(i)) for i,_ in enumerate(demands)} 
    nodeVars = {n: bddvar(str(n)) for n in network.nodes}
    edgeVars = {str(e[0]) + str(e[1]): bddvar(str(e[0]) + str(e[1])) for e in network.edges}

    flow_funcs = {node: isNodeInRoute(network,node,nodeVars, edgeVars) for node in nodeVars}

    demand_clauses = [demand(network,demands[i], d, nodeVars, edgeVars, flow_funcs) for i,d in demandVars.items()]
    bdd = reduce(orl, demand_clauses, demand_clauses[0]) & demand_unique(demandVars)
    drawBDD(bdd, "test", True)
  
generateBDD(G, [("A", "C"), ("B", "C")])


