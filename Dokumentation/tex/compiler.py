#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# Latex.py
# Bernard Schroffenegger
# 23th of September, 2019


""" .tex --> .pdf (pdflatex)
    - arguments: tex-file <str>, target-directory <str> (opt), (number of compilations <int>)
    - usage: $ python Latex.py example.tex ../ 3 """

import os, sys, subprocess
import webbrowser
from pathlib import Path


def main():

    # simple arg-parser
    runs = int(sys.argv[3]) if len(sys.argv) == 4 else 1
    output_dir = sys.argv[2] if len(sys.argv) > 2 else ''
    if len(sys.argv) > 1:
        compile(sys.argv[1], output_dir, runs)


def compile(input_file, output_dir, runs, cleanup=[".log", ".aux", ".out"]):
    """ transforms *.tex into *.pdf, delete pdflatex-doc-files, and open the output
    :param input_file: <str> Path (document)
    :param output_dir: <str> Path (folder)
    :param runs: <int> number of compilations
    :param cleanup: list(str) delete by-product files
    :return: - """

    for _ in range(runs):
        if os.path.exists(input_file):
            pdf = '-output-directory=' + output_dir if output_dir else ''
            cmd = ['pdflatex', '-halt-on-error', '-interaction', 'batchmode', pdf, input_file]
            subprocess.Popen(cmd).communicate()

    for ext in cleanup:
        os.unlink(output_dir + '/' + input_file.split('.')[0] + ext)

    webbrowser.open_new("file://"+str(Path(output_dir+''+input_file.split('.')[0]+'.pdf').absolute()))


if __name__ == '__main__':

    main()
