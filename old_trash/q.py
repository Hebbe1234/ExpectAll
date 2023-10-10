from pyeda.inter import *
from dd.autoref import BDD
import re
from graphviz import Source
import pydot

bdd = BDD()
bdd.declare('x1', 'x2', 'z0', 'z1', 'z2','z3', 'y1','y2')

x1 = bdd.var("x1")
x2 = bdd.var("x2")
z0 = bdd.var("z0")
z1 = bdd.var("z1")
z2 = bdd.var("z2")
z3 = bdd.var("z3")
y1 = bdd.var("y1")
y2 = bdd.var("y2")

T = (~x1 & ~x2 & z0  & ~y1 & y2 ) |\
    (~x1 & ~x2 & ~z0 & y1  & ~y2) |\
    (~x1 & x2  & z1  & y1  & ~y2) |\
    (~x1 & x2  & ~z1 & y1  & y2 ) |\
    (x1  & ~x2 & z2  & y1  & y2 ) |\
    (x1  & ~x2 & ~z2 & ~y1 & y2 ) 


for sol in bdd.pick_iter(T):
    print(sol)
    
print(T)
bdd.collect_garbage()
bdd.dump('test.pdf', roots=[T])

# def removeZeroNode(graphString) : 
#     g = pydot.graph_from_dot_data(graphString)[0]
#     g.write_dot("ssdf1.dot")
#     f = open("ssdf1.dot").read()
#     label0Id = re.search(r'(n.*)\t.*\n\t\tlabel=0',f).group(1)
#     f = re.sub(r'.*{}.*\n.*\n.*\n[^n]*'.format(label0Id),'',f)
#     return f

# x1 = bddvar("x1")
# x2 = bddvar("x2")
# z0 = bddvar("z0")
# z1 = bddvar("z1")
# z2 = bddvar("z2")
# z3 = bddvar("z3")
# y1 = bddvar("y1")
# y2 = bddvar("y2")

# # f = a & b | a & c | b & c


# T = (~x1 & ~x2 & z0  & ~y1 & y2 ) |\
#     (~x1 & ~x2 & ~z0 & y1  & ~y2) |\
#     (~x1 & x2  & z1  & y1  & ~y2) |\
#     (~x1 & x2  & ~z1 & y1  & y2 ) |\
#     (x1  & ~x2 & z2  & y1  & y2 ) |\
#     (x1  & ~x2 & ~z2 & ~y1 & y2 ) 

# b1 = (x1&x2)
# b2 = (x1&x2) | ((~x1&x2&~z1) | (x1&~x2&z2)) 
# print(list(b2.satisfy_all()))
# # myBDD = isBInTheRoute & IsCInTheRoute & flow_a_to_d

# # k = list(myBDD.satisfy_all())
# # print(len(k),k)

# gv = Source(removeZeroNode(b2.to_dot()))
# gv.render('render_pdf_name',view=False)