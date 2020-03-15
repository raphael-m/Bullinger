#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# Pdf2jpg.py
# Bernard Schroffenegger
# 10th of September, 2019

from pdf2image import convert_from_path
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


def main():

    input_path = "Karteikarten/PDF_new"
    output_path = "Karteikarten/PNG_new/HBBW_Karteikarte_"
    # output_path = "App/static/cards/HBBW_Karteikarte_"

    i = 1
    for file in FileSystem.get_file_paths(input_path):
        for page in convert_from_path(file, 300):
            print(file)
            path = output_path+(5-len(str(i)))*'0'+str(i)+'.png'
            page.save(path, 'PNG')
            i += 1


if __name__ == '__main__':

    main()

