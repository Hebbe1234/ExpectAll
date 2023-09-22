from pyeda.inter import *
import re
from graphviz import Source
import pydot

def removeZeroNode(graphString) : 
    g = pydot.graph_from_dot_data(myBDD.to_dot())[0]
    g.write_dot("ssdf1.dot")
    f = open("ssdf1.dot").read()
    label0Id = re.search(r'(n.*)\t.*\n\t\tlabel=0',f).group(1)
    f = re.sub(r'.*{}.*\n.*\n.*\n[^n]*'.format(label0Id),'',f)
    return f

x,y,A,B,C,D,a,b,c,d,e,f,h = map(bddvar, 'xyABCDabcdefh')

# f = a & b | a & c | b & c
isBInTheRoute = ((x & B & ((a & c & ~e) | (a & ~c & e) | (~a & c & e))) | x & (~B & ~a & ~c & ~e))
IsCInTheRoute = ((x & C & ((d & b & ~e) | (b & ~d & e) | (~b & d & e))) | x & (~C & ~b & ~d & ~e))  
flow_a_to_d = ((x & a & ~b) | (x & ~a &b)) &  ((x & ~c & d) | (x &c & ~d)) 


isAInTheRoute = (y & A & a & b) | (y & ~A & ~a & ~b)
isDInTheRoute = (y & D & c & d) | (y & ~D & ~c & ~d)

flow_b_to_c = ((y & a & ~c & ~e) | (y & ~a & c & ~e) | (y & ~a & ~c & e)) & \
            ((y & b & ~d & ~e) | (y & ~b & d & ~e) | (y & ~b & ~d & e))

myBDD = ((flow_b_to_c & isAInTheRoute & isDInTheRoute) |  (flow_a_to_d & isBInTheRoute & IsCInTheRoute) ) & ((x | y) & (~x | ~y))
# myBDD = isBInTheRoute & IsCInTheRoute & flow_a_to_d

# k = list(myBDD.satisfy_all())
# print(len(k),k)

gv = Source(removeZeroNode(myBDD.to_dot()))
gv.render('render_pdf_name',view=True)