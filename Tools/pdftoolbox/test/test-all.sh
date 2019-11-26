#  Collate scanned pages:

   ../bin/pdftoolbox A=sample_even.pdf B=sample_odd.pdf -crossmerge A B -outfile _collated1.pdf

#  or if odd.pdf is in reverse order:

   ../bin/pdftoolbox A=sample_even.pdf B=sample_odd.pdf -crossmerge A Bend-1 -outfile _collated2.pdf

#  Decrypt a PDF:

   ../bin/pdftoolbox sample_secured.pdf -inputpassword 456 -outfile _unsecured.pdf

#  Encrypt a PDF using 128-bit strength:

   ../bin/pdftoolbox sample_verypdf.pdf -outfile _encrypted.128.pdf -ownerpassword 123

#  Set both owner password and open password to a PDF file:

   ../bin/pdftoolbox sample_verypdf.pdf -outfile _encrypted_both.pdf -ownerpassword 456 -userpassword 123

#  Enable High Quality Printing when encrypt a PDF file:

   ../bin/pdftoolbox sample_verypdf.pdf -outfile _encrypted_highprinting.pdf -ownerpassword 456 -userpassword 123 -permit printing

# Merge PDF files into a new PDF.

   ../bin/pdftoolbox sample_even.pdf sample_odd.pdf -merge -outfile _merge_out1.pdf
   ../bin/pdftoolbox A=sample_even.pdf B=sample_odd.pdf -merge A B -outfile _merge_out2.pdf
   
#  or (using wildcards):

   ../bin/pdftoolbox sample_in*.pdf -merge -outfile _combined_all.pdf

#  Remove some page from an input PDF file. The example shows how to remove P13 from the input file.

   ../bin/pdftoolbox sample_testcmd.pdf -merge 1-12 14-end -outfile _remove_pages_1.pdf
   
#  or:

   ../bin/pdftoolbox A=sample_testcmd.pdf -merge A1-12 A14-end -outfile _remove_pages_2.pdf

#  Merge PDF files and add a password for the output file.

   ../bin/pdftoolbox sample_even.pdf sample_odd.pdf -merge -outfile _merge_out.pdf -key40bit -ownerpassword 123

#  Merge PDF files and if one of them requires password,input it.

   ../bin/pdftoolbox A=sample_secured.pdf sample_verypdf.pdf -inputpassword A=123 -merge -outfile _merge_out.pdf

#  Unpack PDF page streams for editing PDF in a text editor.

   ../bin/pdftoolbox sample_verypdf.pdf -outfile _unpack_verypdf.pdf -unpack

#  Repair PDF's corrupted XREF table and stream lengths.

   ../bin/pdftoolbox sample_verypdf.pdf -outfile _verypdf_fixed.pdf

#  Split a multip-page PDF file into single-page PDF files.
#  ../bin/pdftoolbox testcmd.pdf -split

   ../bin/pdftoolbox sample_testcmd.pdf -split -outfile _pg_%%04d.pdf

#  Blast a multip-page PDF file into several encrypted single-page PDF files, denying  low-quality printing.

   ../bin/pdftoolbox sample_secured.pdf -split -ownerpassword 123 -permit lowprinting

#  Extract meta info from input PDF file to the given output file.

   ../bin/pdftoolbox sample_verypdf.pdf -getinfo -outfile _report.txt

#  Rotate the first PDF page clockwise.

   ../bin/pdftoolbox sample_verypdf.pdf -merge 1E 2-end -outfile _rotate_out1.pdf

#  Rotate an entire PDF document to 180 degrees

   ../bin/pdftoolbox sample_verypdf.pdf -merge 1-endS -outfile _rotate_out2.pdf

#  Add information from text file to output PDF file.

   ../bin/pdftoolbox sample_verypdf.pdf -setinfo _report.txt -outfile _newinfo.pdf

#
