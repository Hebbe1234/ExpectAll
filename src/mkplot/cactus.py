#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## cactus.py
##
##  Created on: Jun 05, 2015
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

#
#==============================================================================
import json
import matplotlib.pyplot as plt
from matplotlib import __version__ as mpl_version
import math
import numpy as np
import os
from plot import Plot
import six


#
#==============================================================================
class Cactus(Plot, object):
    """
        Cactus plot class.
    """

    def __init__(self, options):
        """
            Cactus constructor.
        """

        super(Cactus, self).__init__(options)

        with open(self.def_path, 'r') as fp:
            self.linestyles = json.load(fp)['cactus_linestyle']
        
        #SW9, group 7: Hardcode some of the line styles for the experiments we run
        self.hardcoded_linestyles = {
            "rwa-inc": {"c": "blue",     "ms": 5, "lw": 2, "alpha": 0.7, "mfc": "white", "mec": "green",   "mew": 0.75},
            "baseline": {"c": "green",  "ls": "--", "ms": 5, "lw": 2, "alpha": 0.7, "mfc": "white", "mec": "red",     "mew": 0.75},
            "preprocess": {"c": "red",   "ls":"-", "ms": 5, "lw": 2, "alpha": 0.7, "mfc": "white", "mec": "blue",    "mew": 0.75},
            "MIP-all": {"c": "red",   "ls":"-", "ms": 5, "lw": 2, "alpha": 0.7, "mfc": "white", "mec": "blue",    "mew": 0.75},
            "add-last": {"c": "magenta",   "ls":"-.", "ms": 5, "lw": 2, "alpha": 0.7, "mfc": "white", "mec": "blue",    "mew": 0.75},
            "add-full": {"c": "brown",   "ls":":", "ms": 5, "lw": 2, "alpha": 0.7, "mfc": "white", "mec": "blue",    "mew": 0.75},
            "rwa-inc-par": {"c": "brown",   "marker": "+", "ms": 5, "lw": 1, "alpha": 0.7, "mfc": "white", "mec": "brown",   "mew": 0.75},
            "rwa-seq": {"c": "orange",  "marker": "D", "ms": 5, "lw": 1, "alpha": 0.7, "mfc": "white", "mec": "orange",  "mew": 0.75},
            "rwa-lim": {"c": "magenta", "marker": "*", "ms": 5, "lw": 1, "alpha": 0.7, "mfc": "white", "mec": "magenta", "mew": 0.75},
            "rwa-conq-inc-par-lim": {"c": "cyan",    "marker": "o", "ms": 5, "lw": 2, "alpha": 0.7, "mfc": "white", "mec": "cyan",    "mew": 0.75},
            "default-heuristic": {"c": "black",   "marker": "d", "ms": 5, "lw": 2, "alpha": 0.7, "mfc": "white", "mec": "black",   "mew": 0.75},
            "rwa-inc-par-seq-cudd": {"c": "black",   "marker": "d", "ms": 5, "lw": 2, "alpha": 0.7, "mfc": "white", "mec": "black",   "mew": 0.75},
            "default-heuristic-bad": {"c": "red",   "marker": "d", "ms": 5, "lw": 2, "alpha": 0.7, "mfc": "white", "mec": "black",   "mew": 0.75},
            "rwa-conq-par": {"c": "#666aee", "marker": "v", "ms": 5, "lw": 2, "alpha": 0.7, "mfc": "white", "mec": "#666aee", "mew": 0.75},
            "rwa-inc-par-seq": {"c": "grey",    "marker": ">", "ms": 5, "lw": 2, "alpha": 0.7, "mfc": "white", "mec": "grey",    "mew": 0.75},
            "rwa-inc-par-seq-early": {"c": "orange",  "ls":":", "marker": "x", "ms": 5, "lw": 2, "alpha": 0.7, "mfc": "white", "mec": "orange",    "mew": 0.75},
            "split": {"c": "black",  "ls":":", "marker": "o", "ms": 5, "lw": 2, "alpha": 0.7, "mfc": "white", "mec": "orange",    "mew": 0.75},
            "naive": {"c": "brown",  "ls":"-", "marker": "d", "ms": 2, "lw": 2, "alpha": 0.7, "mfc": "white", "mec": "brown",    "mew": 0.75},
            "disjoint": {"c": "blue",  "ls":"-", "marker": "d", "ms": 2, "lw": 2, "alpha": 0.7, "mfc": "white", "mec": "brown",    "mew": 0.75},
            "paths": {"c": "blue",  "ls":"--", "marker": "x", "ms": 2, "lw": 2, "alpha": 0.7, "mfc": "white", "mec": "blue",    "mew": 0.75},
            "paths-inc-par-seq": {"c": "blue",  "ls":"--", "marker": "*", "ms": 5, "lw": 2, "alpha": 0.7, "mfc": "white", "mec": "blue",    "mew": 0.75},
            "split": {"c": "cyan", "marker": "x", "ms": 5, "lw": 1, "alpha": 0.7, "mfc": "white", "mec": "magenta", "mew": 0.75},
        }
        

    def create(self, data):
        """
            Does the plotting.
        """
 
         #SW9, group 7: Hardcode some of the line styles for the experiments we run
        known_names = [res[0] for res in data if res[0] in self.hardcoded_linestyles]
        linestyles = [hl for name, hl in sorted(self.hardcoded_linestyles.items(), key=lambda x: x[0], reverse=True) if str(name) in known_names] + self.linestyles
        
        data = sorted(data, key=lambda x: x[0],reverse=True) #SW9, group 7: to make sure graphs are plotted in same order of colors
        # making ls
        coords = []
        for d in data:
            #arr = list(filter(lambda x: x <= 3600, d[1])) # Used when all 
            arr = list(d[1]) # Used for most stuff
            coords.append(np.arange(1, len(arr) + 1))  # xs (separate for each line)
            
            sort = True #Set to False to stop sorting 
            if sort:
                coords.append(np.array((sorted(arr)))) 
            else:
                coords.append(np.array(((arr)))) 
        lines = plt.plot(*coords, zorder=3)

        # setting line styles
        for i, l in enumerate(lines):
            plt.setp(l, **linestyles[i % len(linestyles)])

        # turning the grid on
        if not self.no_grid:
            plt.grid(True, color=self.grid_color, ls=self.grid_style, lw=self.grid_width, zorder=1)

        # axes limits
        plt.xlim(self.x_min, self.x_max if self.x_max else math.ceil(max([d[2] for d in data]) / float(100)) * 100)
        plt.ylim(self.y_min, self.y_max if self.y_max else self.timeout)

        # axes labels
        if self.x_label:
            plt.xlabel(self.x_label)
        else:
            plt.xlabel('instances')

        if self.y_label:
            plt.ylabel(self.y_label)
        else:
            plt.ylabel('Run time (s)')

        # choosing logarithmic scales if needed
        ax = plt.gca()
        if self.x_log:
            ax.set_xscale('log')
        if self.y_log:
            ax.set_yscale('log')

        # setting ticks
        # plt.xticks(np.arange(self.x_min, self.x_max + 1, 2))
        # if not self.y_log:
        #     # plt.yticks(list(plt.yticks()[0]) + [self.timeout])
        #     ax.set_yticks(range(0, 2 * (int(self.y_max) if self.y_max else int(self.timeout)), 200))

        # setting ticks font properties
        # set_*ticklables() seems to be not needed in matplotlib 1.5.0
        if float(mpl_version[:3]) < 1.5:
            ax.set_xticklabels(ax.get_xticks(), self.f_props)
            ax.set_yticklabels(ax.get_yticks(), self.f_props)

        # SW9 - E23 - Group 7 - Keep integer ticks for small datasets
        ax.set_xticks([t for t in ax.get_xticks() if int(t) == t])


        strFormatter = plt.FormatStrFormatter('%d')
        logFormatter = plt.LogFormatterMathtext(base=10)
        ax.xaxis.set_major_formatter(strFormatter if not self.x_log else logFormatter)
        ax.yaxis.set_major_formatter(strFormatter if not self.y_log else logFormatter)

        # making the legend
        if self.lgd_loc != 'off':
            lgtext = [d[0] for d in data]
            lg = ax.legend(lines, lgtext, ncol=self.lgd_ncol, loc=self.lgd_loc, fancybox=self.lgd_fancy, shadow=self.lgd_shadow if self.lgd_alpha == 1.0 else False) #, prop={"size":14}
            fr = lg.get_frame()
            fr.set_lw(1)
            fr.set_alpha(self.lgd_alpha)
            fr.set_edgecolor('black')

        # setting frame thickness
        for i in six.itervalues(ax.spines):
            i.set_linewidth(1)    

        plt.savefig(self.save_to, bbox_inches='tight', transparent=self.transparent)
