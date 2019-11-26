#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# Karteikarten.py
# Bernard Schroffenegger
# 1st of September, 2019

import os, re
from pathlib import Path
from PyPDF2 import PdfFileWriter, PdfFileReader


def main():

    input_pdf = 'Karteikarten/PDF/'
    input_xml = 'Karteikarten/OCR/'
    """
    for p in os.listdir(input_xml):
        m = re.match(r'.*_(\d+).xml', p)

    
    SORT
    ====
    
    # Create Directories 1, 101, 201, ..., 10'001
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
        #count = sum([1 for file in datafiles])
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
        #count = sum([1 for file in datafiles])
        for dir in directories:
            for p, di, da in os.walk(path+dir):
                for d in da:
                    a = os.path.join(p, d)
                    if os.path.isfile(a) and not a.endswith(".DS_Store"):
                        list1.append(a)

    list2 = []
    for path, directories, datafiles in os.walk(input_xml):
        #count = sum([1 for file in datafiles])
        for dir in directories:
            for p, di, da in os.walk(path+dir):
                for d in da:
                    a = os.path.join(p, d)
                    if os.path.isfile(a) and not a.endswith(".DS_Store"):
                        list2.append(d)

    print(len(list1), len(list2))
    #print(list1, list2)


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
                #print(p+"/"+s, "\t", input_pdf+'HBBW_Karteikarte_'+x*'0'+str(i)+'.pdf')
                #Path(p+"/"+s).rename(input_pdf+'HBBW_Karteikarte_'+x*'0'+str(i)+'.pdf')
                #print(input_pdf+'HBBW_Karteikarte_'+x*'0'+str(i)+'.pdf')
                i += 1

        if m:
            _id = m.group(1)
            zeros = (5 - len(_id))*'0'
            Path(input_xml+p).rename(input_xml + 'HBBW_Karteikarte_' + zeros + _id + '.xml')
        else:
            print(p)

    """

""" PDF
Karteikarten/All/karteikarten_bullinger_komplett/3701 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/5601 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/701 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/1201 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/7901 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/9401 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/7301 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/1801 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/9001 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/901 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/7701 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/301 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/1601 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/5201 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/3901 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/3301 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/10001 	#Files: 93          (<-- ok)
Karteikarten/All/karteikarten_bullinger_komplett/5801 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/8001 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/6701 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/4201 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/2901 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/2301 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/4801 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/2701 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/4601 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/6901 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/8401 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/6301 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/401 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/1101 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/9701 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/7001 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/3401 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/5501 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/5101 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/3001 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/9301 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/7401 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/9901 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/1501 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/4101 	#Files: 51          <--------- 4101
Karteikarten/All/karteikarten_bullinger_komplett/2001 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/8301 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/6401 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/8901 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/1 	    #Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/8701 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/6001 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/2401 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/4501 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/7101 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/9601 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/1001 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/501 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/5401 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/3501 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/3101 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/5001 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/1401 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/101 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/9801 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/7501 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/9201 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/2101 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/4001 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/8801 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/6501 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/8201 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/6101 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/8601 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/4401 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/2501 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/5701 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/3601 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/1901 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/7201 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/9501 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/7801 	#Files: 51                  <---------- 7801
Karteikarten/All/karteikarten_bullinger_komplett/1301 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/601 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/1701 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/201 	#Files: 51                  <---------- 201
Karteikarten/All/karteikarten_bullinger_komplett/7601 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/801 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/9101 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/5901 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/3201 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/3801 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/5301 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/6601 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/8101 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/4901 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/2201 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/2801 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/4301 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/4701 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/2601 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/6201 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/8501 	#Files: 100
Karteikarten/All/karteikarten_bullinger_komplett/6801 	#Files: 100
"""



""" XML

Karteikarten/All/karteikarten_bullinger_ocr/3701 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/5601 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/701 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/1201 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/7901 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/9401 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/7301 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/1801 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/9001 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/901 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/7701 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/301 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/1601 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/5201 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/3901 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/3301 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/10001 	#Files: 94          <-- ok
Karteikarten/All/karteikarten_bullinger_ocr/5801 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/8001 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/6701 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/4201 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/2901 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/2301 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/4801 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/2701 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/4601 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/6901 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/8401 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/6301 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/401 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/1101 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/9701 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/7001 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/3401 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/5501 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/5101 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/3001 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/9301 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/7401 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/9901 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/1501 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/4101 	#Files:     149             <------------- 4101
Karteikarten/All/karteikarten_bullinger_ocr/2001 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/8301 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/6401 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/8901 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/1 	    #Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/8701 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/6001 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/2401 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/4501 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/7101 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/9601 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/1001 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/501 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/5401 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/3501 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/3101 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/5001 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/1401 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/101 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/9801 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/7501 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/9201 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/2101 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/4001 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/8801 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/6501 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/8201 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/6101 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/8601 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/4401 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/2501 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/5701 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/3601 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/1901 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/7201 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/9501 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/7801 	#Files:     149             <------------- 7801        
Karteikarten/All/karteikarten_bullinger_ocr/1301 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/601 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/1701 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/201 	#Files:     149             <------------- 201
Karteikarten/All/karteikarten_bullinger_ocr/7601 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/801 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/9101 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/5901 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/3201 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/3801 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/5301 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/6601 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/8101 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/4901 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/2201 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/2801 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/4301 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/4701 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/2601 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/6201 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/8501 	#Files: 101
Karteikarten/All/karteikarten_bullinger_ocr/6801 	#Files: 101
"""

if __name__ == '__main__':

    main()
