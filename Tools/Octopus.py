#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# Octobus.py
# Bernard Schroffenegger
# 30th of November, 2019

""" Kraken: OCR system forked from octopus
        - http://kraken.re/
        - https://github.com/mittagessen/kraken
        - Language Model:
"""

import subprocess

IN = 'App/static/cards/HBBW_Karteikarte_00001.png'
OUT = 'Karteikarten/OCR_Kraken/HBBW_Karteikarte_00001.ocr'
MODEL = 'Tools/ocr_models/en_best.mlmodel'


class Octopus:

    @staticmethod
    def run(input_path, output_path):
        return subprocess.Popen(
            [' '.join(["kraken -i", input_path, output_path, "binarize segment ocr -a -m", MODEL])],
            shell=True
        )
