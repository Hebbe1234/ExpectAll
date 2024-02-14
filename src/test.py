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

import dd.autoref as dd

import networkx as nx
from networkx import digraph
from networkx import MultiDiGraph
import math
from demands import Demand
from itertools import permutations
from bdd import *


mybdd = dd.BDD()

mybdd.declare('x','y','z')

u = mybdd.add_expr(r"x/\y")

v = mybdd.let({"x":"z"},u)

print(mybdd.vars.keys())

print(v)
print(mybdd.to_expr(v))
