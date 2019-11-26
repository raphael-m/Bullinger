#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# Plots.py
# Bernard Schroffenegger
# 6th of October, 2019

import pandas as pd
import matplotlib.pyplot as plt

# colors ('black'/'b', 'white'/'w')
cb0, cb1, cb2, cb3 = 'royalblue', 'cornflowerblue', 'dodgerblue', 'navy'  # 'b'
cg0, cg1, cg2, cg3 = 'forestgreen', 'darkgreen', 'yellowgreen', 'olivedrab'  # 'g'
cr0, cr1, cr2, cr3 = 'orangered', 'firebrick', 'tomato', 'salmon'  # 'r'
cp0, cp1, cp2, cp3 = 'purple', 'indigo', 'orchid', 'plum'  # 'm'
cga, cgb, cgc, cgd = 'slategray', 'dimgrey', 'darkgrey', 'lightgray'  # 'grey'/'gray'
# gold, silver, 'teal', 'chocolate', ...
# More: https://i.stack.imgur.com/lFZum.png


class ScatterPlot:

    def __init__(self, x, y, alpha=0.7, color='b'):
        self.x, self.y = x, y
        self.alpha = alpha
        self.color = color

    @staticmethod
    def create(x, y, alpha=1, color='b', size=10,
               title='', xlabel='', ylabel='',
               output_path=None, show=True,
               x_min=None, x_max=None,y_min=None, y_max=None,
               x_ticks=None, y_ticks=None,
               reverse_x=False, reverse_y=False,
               function=None):
        if isinstance(alpha, list) and isinstance(size, list):
            for i, a in enumerate(alpha):
                plt.scatter(x[i], y[i], alpha=a, s=len(x[i])*[size[i]], color=color[i])
        else: plt.scatter(x, y, alpha=alpha, s=len(x)*[size], color=color)
        if function: function(plt)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.xticks(x_ticks) if x_ticks else None  # e.g. np.arange(0, 1, step=0.2)
        plt.yticks(y_ticks) if y_ticks else None
        axes = plt.gca()
        axes.set_xlim([x_min, x_max]) if x_min and x_max else None
        axes.set_ylim([y_min, y_max]) if y_min and y_max else None
        plt.xlim(plt.xlim()[::-1]) if reverse_x else None
        plt.ylim(plt.ylim()[::-1]) if reverse_y else None
        fig = plt.gcf()  # get current figure
        if output_path:
            plt.draw()
            fig.savefig(output_path, dpi=200)
        plt.show() if show else plt.close(fig)

