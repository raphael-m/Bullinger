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

import subprocess, os, psutil, shutil

IN = 'App/static/cards/HBBW_Karteikarte_00001.png'
OUT = 'Karteikarten/OCR_Kraken/HBBW_Karteikarte_00001.ocr'
MODEL = 'Tools/ocr_models/en_best.mlmodel'


class FileSystem:

    def __init__(self):
        pass

    @staticmethod
    def get_file_paths(dir_path, recursively=True):
        """ returns paths of all datafiles within a directory (recursively)
            :param dir_path: <string> (directory)
            :param recursively: <bool> (current dir/subdirs)
            :return: list(<string>) (file paths) """
        paths = []
        if recursively:
            for path, directories, datafiles in os.walk(dir_path):
                paths += [os.path.join(path, file) for file in datafiles if not file.endswith(".DS_Store")]
        else:
            for file in os.listdir(dir_path):
                p = os.path.join(dir_path, file)
                if os.path.isfile(p) and not file.endswith(".DS_Store"):
                    paths.append(p)
        return sorted(paths)

    @staticmethod
    def file_path_generator(dir_path, recursively=True):
        """ YIELD: the same function as above, just as generator """
        if recursively:
            for path, directories, datafiles in os.walk(dir_path):
                for file in datafiles:
                    yield os.path.join(path, file)
        else:
            for file in os.listdir(dir_path):
                p = os.path.join(dir_path, file)
                if os.path.isfile(p):
                    yield p

    @staticmethod
    def get_number_of_files(dir_path, recursively=True):
        return len(FileSystem.get_file_paths(dir_path, recursively=recursively))

    @staticmethod
    def delete_all_recursively(path):
        """ delete directory regardlessly """
        shutil.rmtree(path)


class Octopus:

    @staticmethod
    def run(input_path, output_path):
        return subprocess.Popen(
            [' '.join(["kraken -i", input_path, output_path, "binarize segment ocr -a -m", MODEL])],
            shell=True
        )

    @staticmethod
    def run_ocr_octopus():
        """ caution: takes 1-2 weeks for all 10'093 files """
        in_out_pairs = []

        root = "Karteikarten/PNG_new"
        input_path = "Karteikarten/PNG_new/HBBW_Karteikarte_"
        output_path = "Karteikarten/OCR_new/HBBW_Karteikarte_"

        i = 1
        for _ in FileSystem.get_file_paths(root):
            file_in = input_path + (5 - len(str(i))) * '0' + str(i) + '.png'
            file_out = output_path + (5 - len(str(i))) * '0' + str(i) + '.ocr'
            in_out_pairs.append([file_in, file_out])
            i += 1

        for pair in in_out_pairs:
            print(pair[0], "-->", pair[1])
            sub_process = Octopus.run(pair[0], pair[1])
            p = psutil.Process(sub_process.pid)
            try:
                p.wait(timeout=60 * 1.5)
            except psutil.TimeoutExpired:
                p.kill()
                continue

def main():

    Octopus.run_ocr_octopus()


if __name__ == '__main__':

    main()
