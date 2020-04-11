#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# Plots.py
# Bernard Schroffenegger
# 6th of October, 2019
import statistics

from Tools.BullingerData import *
import matplotlib.pyplot as plt
import numpy as np
plt.rcdefaults()


# colors ('black'/'b', 'white'/'w')
cb0, cb1, cb2, cb3 = 'royalblue', 'cornflowerblue', 'dodgerblue', 'navy'  # 'b'
cg0, cg1, cg2, cg3 = 'forestgreen', 'darkgreen', 'yellowgreen', 'olivedrab'  # 'g'
cr0, cr1, cr2, cr3 = 'orangered', 'firebrick', 'tomato', 'salmon'  # 'r'
cp0, cp1, cp2, cp3 = 'purple', 'indigo', 'orchid', 'plum'  # 'm'
cga, cgb, cgc, cgd = 'slategray', 'dimgrey', 'darkgrey', 'lightgray'  # 'grey'/'gray'
# gold, silver, ...
# More: https://i.stack.imgur.com/lFZum.png

ROUND = 0


class ScatterPlot:

    def __init__(self, x, y, alpha=0.7, color='b'):
        self.x, self.y = x, y
        self.alpha = alpha
        self.color = color

    @staticmethod
    def create(x, y, alpha=1, color='b', size=10,
               title='', xlabel='', ylabel='',
               x_min=None, x_max=None, y_min=None, y_max=None,
               x_ticks=None, y_ticks=None,
               output_path=None, show=True,
               reverse_x=False, reverse_y=False,
               function=None):
        if isinstance(alpha, list) and isinstance(size, list):
            for i, a in enumerate(alpha):
                plt.scatter(x[i], y[i], alpha=a, s=len(x[i]) * [size[i]], color=color[i])
        else:
            plt.scatter(x, y, alpha=alpha, s=len(x) * [size], color=color)
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


# Bullinger specific
def stats(df, columns=None):
    """ averages and standard deviations
        :param columns: <list(int)>. indices
        :param df: <DataFrame>
        :return: <DataFrame> """
    s = ['axis', 'mean', 'dev']
    d = pd.DataFrame(columns=s)
    for column in columns:
        mean = round(sum(df.loc[:, column]) / len(list(df.loc[:, column])), ROUND)
        std_dev = round(statistics.stdev(df.loc[:, column]), ROUND)
        d = pd.concat([d, pd.DataFrame({s[0]: [column], s[1]: [mean], s[2]: std_dev})])
    return d


def draw_grid(plt):
    """ appends the grid of a typical index card to plot <plt> """
    x0, x1, x2, x3 = 0, 3057, 6508, 9860
    y0, y1, y2, y3, y4, y5, y6, y7, y8 = 0, 1535, 2041, 2547, 3053, 3559, 4257, 5303, 6978
    alpha, linewidth = 0.3, 0.5

    # Vertical Lines
    plt.plot((x0, x0), (y0, y8), 'black', alpha=alpha, linewidth=linewidth)
    plt.plot((x1, x1), (y0, y8), 'black', alpha=alpha, linewidth=linewidth)
    plt.plot((x2, x2), (y0, y5), 'black', alpha=alpha, linewidth=linewidth)
    plt.plot((x3, x3), (y0, y8), 'black', alpha=alpha, linewidth=linewidth)

    # Horizontal Lines
    plt.plot((x0, x3), (y0, y0), 'black', alpha=alpha, linewidth=linewidth)
    plt.plot((x0, x3), (y1, y1), 'black', alpha=alpha, linewidth=linewidth)
    plt.plot((x0, x3), (y2, y2), 'black', alpha=alpha, linewidth=linewidth)
    plt.plot((x0, x3), (y3, y3), 'black', alpha=alpha, linewidth=linewidth)
    plt.plot((x0, x3), (y4, y4), 'black', alpha=alpha, linewidth=linewidth)
    plt.plot((x0, x3), (y5, y5), 'black', alpha=alpha, linewidth=linewidth)
    plt.plot((x0, x1), (y6, y6), 'black', alpha=alpha, linewidth=linewidth)
    plt.plot((x1, x3), (y7, y7), 'black', alpha=alpha, linewidth=linewidth)
    plt.plot((x0, x3), (y8, y8), 'black', alpha=alpha, linewidth=linewidth)


class BarChart:

    @staticmethod
    def create_plot_overview(file_id, offen, abgeschlossen, unklar, ungueltig):
        fig = plt.figure()
        bars = ('offen', 'abgeschlossen', 'unklar', 'ungültig')
        y_pos = np.arange(len(bars))
        performance = [offen, abgeschlossen, unklar, ungueltig]
        plt.bar(y_pos, performance, align='center', alpha=0.5)
        plt.xticks(y_pos, bars)
        plt.ylabel('Anzahl Karteikarten')
        fig.savefig('App/static/images/plots/overview_' + file_id + '.png')
        plt.close()


class PieChart:

    @staticmethod
    def create_plot_overview_stats(file_id, sizes, labels, colors):
        fig = plt.figure()
        explode = (0, 0.2, 0, 0)
        patches, texts = plt.pie(sizes, explode=explode, colors=colors, shadow=True, startangle=90)
        plt.legend(patches, labels, loc="upper right")
        plt.axis('equal')
        plt.tight_layout()
        fig.savefig('App/static/images/plots/overview_'+file_id+'.png')
        plt.close()
        return 'images/plots/overview_'+file_id+'.png'


