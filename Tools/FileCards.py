#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# xml.py
# Bernard Schroffenegger
# 13th of November, 2019

""" basing on OCR V2 """

import statistics
from Tools.OCR2 import *
from Tools.Plots import *

SCHEMA_STATS = ['axis', 'mean', 'dev']


class FileCards:

    def __init__(self):
        pass

    @staticmethod
    def plot_page_sizes(dir_path):

        df = OCR2.get_page_sizes(dir_path)
        x, y, mean = list(df)[1], list(df)[2], SCHEMA_STATS[1]  # column names
        avg = list(FileCards.stats(df, columns=[x, y]).loc[:, mean])  # stats


        df_regular = df[(df.x > 9500) & (df.y > 6500) & (df.y < 10000)]
        df_irregular = df[(df.x <= 9500) & (df.y <= 6500) | (df.y >= 10000)]

        print("Number of outliers:", len(list(df_irregular.x)))
        print("Averages: xm =", avg[0], "\t ym =", avg[1])
        ScatterPlot.create(
            [df_regular[x], df_irregular[x], [avg[0]]],  # x-values, avg(x)
            [df_regular[y], df_irregular[y], [avg[1]]],  # y-values, avg(y)
            alpha=[0.3, 0.3, 0.1],  # transparency
            color=['blue', 'orange', 'red'],
            size=[100, 100, 1000],
            title="Karteikartengrösse",
            xlabel="Breite [px]", ylabel="Höhe [px]",
            # output_path=BullingerData.IMG_PAGE_DIM_1
        )



        """
        # Plot (without outliers)
        df = df1[df1.x > 6000]  # 4/99
        sdf = list(BullingerData.stats(df, columns=[x, y]).loc[:, mean])
        ScatterPlot.create(
            [df[x], [sdf[0]]],
            [df[y], [sdf[1]]],
            alpha=[0.3, 0.5], color=['b', 'r'], size=[10, 100],
            xlabel="width [px]", ylabel="height [py]",
            output_path=BullingerData.IMG_PAGE_DIM_2
        )
        """

    @staticmethod
    def stats(df, columns=None):
        """ computes averages and standard deviations of values in a column
            :param df: <DataFrame>
            :param columns: <list(<int>)> or <list(<str>)> (column indices or names)
            :return: <DataFrame> """
        s = SCHEMA_STATS
        d = pd.DataFrame(columns=s)
        for column in columns:
            mean = round(sum(df.loc[:, column]) / len(list(df.loc[:, column])), 0)
            std_dev = round(statistics.stdev(df.loc[:, column]), 0)
            d = pd.concat([d, pd.DataFrame({s[0]: [column], s[1]: [mean], s[2]: std_dev})])
        return d
