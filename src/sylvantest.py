from dd.sylvan import Function
from dd.sylvan import BDD as _BDD

bdd = _BDD()

bdd.declare("x","y","z")

u = bdd.add_expr(r'x /\ y')

v = bdd.exist(['x'], u)