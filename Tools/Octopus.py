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

    '''
    @staticmethod
    def run_ocr_octopus():
        """ caution: takes 1-2 weeks for all 10'093 files """
        
        in_out_pairs = []
        file_ids = [k.id_brief for k in Kartei.query.all()]
        for i in file_ids:
            file_out = 'Karteikarten/OCR_Kraken/HBBW_Karteikarte_' + (5 - len(str(i))) * '0' + str(i) + '.ocr'
            if not os.path.exists(file_out):
                file_in = 'App/static/cards/HBBW_Karteikarte_' + (5 - len(str(i))) * '0' + str(i) + '.png'
                in_out_pairs.append([file_in, file_out])
        for pair in in_out_pairs:
            print(pair[1])
            sub_process = Octopus.run(pair[0], pair[1])
            p = psutil.Process(sub_process.pid)
            try:
                p.wait(timeout=60 * 1.5)
            except psutil.TimeoutExpired:
                p.kill()
                continue
    '''
