#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# FileSystem.py
# Bernard Schroffenegger
# 29th of September, 2019

import os
import shutil


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
