from pyeda.inter import *
import re
from graphviz import Source
import pydot

def removeZeroNode(graphString):
        g = pydot.graph_from_dot_data(graphString)[0]
        g.write_dot("./out/cleaning.dot")
        f = open("./out/cleaning.dot").read()
        label0Id = re.search(r"(n.*)\t.*\n\t\tlabel=0", f).group(1)
        f = re.sub(r".*{}.*\n.*\n.*\n[^n]*".format(label0Id), "", f)
        f = re.sub(r"\[label=[01],", "[", f)
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


x1 = bddvar('x1')
x2 = bddvar('x2')
z0 = bddvar('z0')
z1 = bddvar('z1')

B3_r_v2 = (x1 & ~x2) | (~x1 & x2 & ~z1) | (~x1 & ~x2 & z0) | (~x1 & ~x2 & ~z0 & ~z1) | (~x1 & x2 & z0 & z1)  




z0 = bddvar('z0')
z1 = bddvar('z1')
zz0 = bddvar('zz0')
zz1 = bddvar('zz1')

U_r_v2 = (z0 | (~z0 & ~z1)) & (zz0 | (~zz0 & ~zz1)) &\
        ((z0 & ~zz0 & ((z1 & zz1)|(~z1 & ~zz1))) | (z1 & ~zz1 & ((z0 & zz0)|(~z0 & ~zz0))) ) 

# myBDD = isBInTheRoute & IsCInTheRoute & flow_a_to_d

# k = list(myBDD.satisfy_all())
# print(len(k),k)

gv = Source(removeZeroNode(U_r_v2.to_dot()))
gv.render('render_pdf_name',view=True)