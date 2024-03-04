try:
	from dd.sylvan import Function
	from dd.sylvan import BDD as _BDD
except ImportError:
	from dd.cudd import Function
	from dd.cudd import BDD as _BDD
	print("using cudd")


bdd = _BDD()

bdd.declare("x","y","z")

u = bdd.add_expr(r'x /\ y')

v = u.exist(*['x'])