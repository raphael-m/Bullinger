#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# Pdf2jpg.py
# Bernard Schroffenegger
# 10th of September, 2019

from pdf2image import convert_from_path
from Tools.FileSystem import FileSystem


def main():

    input_path = "Karteikarten/PDF_new"
    output_path = "Karteikarten/PNG_new/HBBW_Karteikarte_"
    # output_path = "App/static/cards/HBBW_Karteikarte_"

    i = 1
    for file in FileSystem.get_file_paths(input_path):
        for page in convert_from_path(file, 600):
            print(file)
            path = output_path+(5-len(str(i)))*'0'+str(i)+'.png'
            page.save(path, 'PNG')
            i += 1


if __name__ == '__main__':

    main()
