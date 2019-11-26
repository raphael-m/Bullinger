#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# Latex.py
# Bernard Schroffenegger
# 23th of September, 2019


""" """

import os, sys, subprocess
import webbrowser
from pathlib import Path


class Latex:

    def __init__(self):
        pass

    def output_as_table(self, list_of_lists):
        pass

    @staticmethod
    def compile(input_file, output_dir, runs):
        """ transforms *.tex into *.pdf, delete pdflatex-doc-files, and open the output
        :param input_file: <str> Path (document)
        :param output_dir: <str> Path (folder)
        :param runs: <int> number of compilations """
        for _ in range(runs):
            if os.path.exists(input_file):
                pdf = '-output-directory=' + output_dir if output_dir else ''
                cmd = ['pdflatex', '-halt-on-error', '-interaction', 'batchmode', pdf, input_file]
                subprocess.Popen(cmd).communicate()

        for ext in [".log", ".aux", ".out", ".toc"]:
            try:
                os.unlink(output_dir + '/' + input_file.split('.')[0] + ext)
            except: pass  # files doesn't exist

        webbrowser.open_new("file://"+str(Path(output_dir+''+input_file.split('.')[0]+'.pdf').absolute()))

