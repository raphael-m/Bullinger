#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# Langid.py
# Bernard Schroffenegger
# 18th of October, 2019

from Tools.langid import *


class Langid:

    config = ['de', 'la', 'el', 'fr']
    langid.set_languages(config)

    @staticmethod
    def classify(s):
        if s:
            lang = langid.classify(s)[0]
            return {
                'de': 'Deutsch',
                'la': 'Latein',
                'el': 'Griechisch',
                'fr': 'Französisch'
            }[lang]
        else: return None
