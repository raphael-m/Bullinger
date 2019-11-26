#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# Dictionaries.py
# Bernard Schroffenegger
# 29th of September, 2019

""" different dictionary types """

import operator
import unittest

from collections import defaultdict
from collections.abc import Iterable


class CountDict(defaultdict):

    """ dict: key --> count <int> """

    def __init__(self):
        super(CountDict, self).__init__(int)  # int <-> lambda: 0
        self.tot = 0  # total number of keys added

    def add(self, key):
        self[key] += 1
        self.tot += 1

    def remove(self, key):
        if key in self:
            if self[key] < 2:
                del self[key]
            else:
                self[key] -= 1
            self.tot -= 1
            return True
        else: return False

    def get_pairs_sorted(self, by_value=False, reverse=False):
        """ [(key_0, value_0), (k1, v1), ..., (k2, v2), (kn, vn)]
            :param by_value: <bool> else by key (actually <int>)
            :param reverse: <bool> (True=descending)
            :return: ordered list of pairs """
        return sorted(self.items(), key=operator.itemgetter(by_value), reverse=reverse)

    @staticmethod
    def combine(dict_list):
        """ unification of several counts
        :param dict_list: [<CountDict>]
        :return: <CountDict> """
        merge = CountDict()
        for d in dict_list:
            for key in d:
                merge[key] += d[key]
            merge.tot += d.tot
        return merge


class ListDict(defaultdict):

    """ dict: key --> [] (multiple values) """

    def __init__(self):
        super(ListDict, self).__init__(list)  # [] <-> lambda: list
        self.tot = 0  # total number of values (within the lists)

    def add(self, key, value):
        if isinstance(value, list):
            self[key] += value
            self.tot += len(value)
        else:
            self[key].append(value)
            self.tot += 1

    def remove(self, key, value):
        if value in self[key]:
            if len(self[key]) < 2:
                del self[key]
            else:
                self[key].remove(value)
            self.tot -= 1
            return True
        else: return False

    @staticmethod
    def combine(dict_list):
        """ unification of dicts to one ListDict
            :param dict_list:
            :return: <ListDict> """
        r = ListDict()  # result: merge all in one
        for d in dict_list:
            for k in d:  # key in dictionary
                if isinstance(d[k], Iterable):
                    r[k] += d[k]
                    r.tot += len(d[k])
                else:  # non <list> dicts
                    r[k] += [d[k]]
                    r.tot += 1
        return r


class TestDictClasses(unittest.TestCase):

    """ Demo/Test """

    def test_count_dict(self):
        d1, d2 = CountDict(), CountDict()
        self.assertEqual(d1[0], 0)
        self.assertEqual(d1.remove('a'), False)
        d1.add('a')
        d1.add('a')
        self.assertEqual(d1['a'], 2)
        self.assertEqual(d1.tot, 2)
        d1.remove('a')
        self.assertEqual(d1['a'], 1)
        self.assertEqual(d1.tot, 1)
        d2.add('b')
        d = CountDict.combine([d1, d2])
        self.assertEqual(d['a'], 1)
        self.assertEqual(d['b'], 1)
        self.assertEqual(d.tot, 2)

    def test_list_dict(self):
        d1, d2 = ListDict(), ListDict()
        d1.add(0, 'a')
        d1.add(0, 'a')
        self.assertListEqual(d1[0], ['a', 'a'])
        d2.add(1, 'b')
        d2.add(1, ['c', 'd'])
        self.assertListEqual(d2[1], ['b', 'c', 'd'])
        d3 = CountDict()
        d3.add(0)
        d = ListDict.combine([d1, d2, d3])
        self.assertListEqual(d[0], ['a', 'a', 1])
        self.assertListEqual(d[1], ['b', 'c', 'd'])
