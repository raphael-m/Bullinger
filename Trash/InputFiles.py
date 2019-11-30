#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# Karteikarten.py
# Bernard Schroffenegger
# 1st of September, 2019

import os, re
from pathlib import Path
from PyPDF2 import PdfFileWriter, PdfFileReader

""" fixing the file index """


def main():

    input_pdf = 'Karteikarten/PDF/DANGEROUS'
    input_xml = 'Karteikarten/OCR/DANGEROUS'

    for p in os.listdir(input_xml):
        m = re.match(r'.*_(\d+).xml', p)

    i = 1
    while i < 10101:
        os.makedirs(input_pdf+str(i))
        i += 100
    
    # Copy Files (Single Pages)
    for file in os.listdir(input_pdf):
        path = os.path.join(input_pdf, file)
        if os.path.isfile(path):
            match = re.search(r'.*\d+_(.*)_Karteikarte.*', path)
            if match:
                dir_name = match.group(1)
                Path(path).rename(input_pdf+dir_name+"/"+file)
    
    # Split/Copy
    for file in os.listdir(input_pdf):
        path = os.path.join(input_pdf, file)
        if os.path.isfile(path) and not path.endswith(".DS_Store"):
            file_name = re.search(r'.*/(\d+_Karteikarte.*)', path, re.M).group(1)
            dir_name = re.search(r'.*/(\d+)_Karteikarte.*', path, re.M).group(1)
            pdf = PdfFileReader(open(path, "rb"))
            for i in range(pdf.numPages):
                output = PdfFileWriter()
                output.addPage(pdf.getPage(i))
                with open(input_pdf+dir_name+"/"+str(i+1)+"_"+file_name, "wb") as outputStream:
                    output.write(outputStream)

    # Create Directories 1, 101, 201, ..., 10'001
    i = 1
    while i < 10101:
        os.makedirs(input_xml + str(i))
        i += 100

    # Copy Files (Single Pages)
    for file in os.listdir(input_xml):
        path = os.path.join(input_xml, file)
        if os.path.isfile(path):
            match1 = re.search(r'[/|_](\d+)_Karteikarte.*', path)
            if match1:
                dir_name = match1.group(1)
                Path(path).rename(input_xml + dir_name + "/" + file)
    
    s = 0
    for path, directories, datafiles in os.walk(input_pdf):
        # count = sum([1 for file in datafiles])
        for dir in directories:
            for p, di, da in os.walk(path+dir):
                print(path+dir, "\t#Files:", sum([1 for f in da]))
                s += sum([1 for f in da])
    print(s)

    count = 0
    for path, directories, datafiles in os.walk(input_xml):
        for dir in directories:
            for p, di, da in os.walk(path+dir):
                for file in da:
                    if re.search(r'.*result.*', file):
                        os.remove(path+dir+"/"+file)
                        count += 1
    print(count)

    path = input_pdf+"7801/"+"1_7801_Karteikarten_HBBW 1547-10-01_1575.pdf"
    pdf = PdfFileReader(open(path, "rb"))
    for i in range(pdf.numPages):
        output = PdfFileWriter()
        output.addPage(pdf.getPage(i))
        name = input_pdf+"7801"+"/"+str(i+51)+"_51_7801_Karteikarten_HBBW 1547-10-01_1575.pdf"
        with open(name, "wb") as outputStream:
            output.write(outputStream)
    
    list1 = []
    for path, directories, datafiles in os.walk(input_pdf):
        # count = sum([1 for file in datafiles])
        for dir in directories:
            for p, di, da in os.walk(path+dir):
                for d in da:
                    a = os.path.join(p, d)
                    if os.path.isfile(a) and not a.endswith(".DS_Store"):
                        list1.append(a)

    list2 = []
    for path, directories, datafiles in os.walk(input_xml):
        # count = sum([1 for file in datafiles])
        for dir in directories:
            for p, di, da in os.walk(path+dir):
                for d in da:
                    a = os.path.join(p, d)
                    if os.path.isfile(a) and not a.endswith(".DS_Store"):
                        list2.append(d)

    print(len(list1), len(list2))
    # print(list1, list2)

    for path, directories, datafiles in os.walk(input_xml):
        b = sorted([dir for dir in directories], reverse=False)
        print(b)
        for c in b:
            for p, di, da in os.walk(path+c):
                for d in da:
                    a = os.path.join(p, d)
                    if os.path.isfile(a) and not a.endswith(".DS_Store"):
                        pass
    n, l = 1, []
    while n<10101:
        l.append(n)
        n += 100
    paths = [os.path.join(input_pdf, str(i)) for i in l]
    i = 1
    for p in paths:
        r = sorted([q for q in os.listdir(p)])
        print(len(r))
        for s in r:
            x = 5-len(str(i))
            if os.path.isfile(p+"/"+s) and not (p+"/"+s).endswith(".DS_Store"):
                # Path(p+"/"+s).rename(input_pdf+'HBBW_Karteikarte_'+x*'0'+str(i)+'.pdf')
                i += 1
        if m:
            _id = m.group(1)
            zeros = (5 - len(_id))*'0'
            Path(input_xml+p).rename(input_xml + 'HBBW_Karteikarte_' + zeros + _id + '.xml')
        else:
            print(p)


if __name__ == '__main__':

    main()
