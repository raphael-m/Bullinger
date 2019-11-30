#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# NGrams.py
# Bernard Schroffenegger
# 6th of October, 2019

from Tools.Dictionaries import CountDict


class NGrams:

    @staticmethod
    def create_n_gram_dict(n, string):
        """ :param n: <int> 1..n
            :param string: <str> """
        dict_n_gram_count = CountDict()
        boundaries = (n - 1) * '_'
        test = boundaries + string + boundaries
        for i in range(len(test) + 1 - n):
            dict_n_gram_count.add(test[i: i + n])
        return dict_n_gram_count

    @staticmethod
    def compute_dice(dict1, dict2):
        d1, c1 = dict1, dict1.tot
        d2, c2 = dict2, dict2.tot
        return -1 if c1+c2 == 0 else 2.0 * NGrams.compute_number_of_common_values(d1, d2) / (c1 + c2)

    @staticmethod
    def compute_number_of_common_values(dict1, dict2):
        return sum([min(dict1[key], dict2[key]) for key in dict1 if key in dict2])
