#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# Pdf2jpg.py
# Bernard Schroffenegger
# 5th of March, 2019


from PyPDF2 import PdfFileWriter, PdfFileReader

inputpdf = PdfFileReader(open("Karteikarten/HBBW_1548_1575.pdf", "rb"))

for i in range(inputpdf.numPages):
    output = PdfFileWriter()
    output.addPage(inputpdf.getPage(i))
    with open("Karteikarten/PDF_new/HBBW_Karteikarte_"+(5-len(str(i+1)))*'0'+str(i+1)+".pdf", "wb") as outputStream:
        output.write(outputStream)
