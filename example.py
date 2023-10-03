from pyeda.inter import *
import re
from graphviz import Source
import pydot


def drawBDD(bdd, outputFileName, clean=True):
    def removeZeroNode(graphString):
        g = pydot.graph_from_dot_data(graphString)[0]
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
