=======================================================
VeryPDF PDFToolbox v 2.0
Copyright (C) 2005-2012 VeryPDF.com, Inc.
Web: http://www.verypdf.com/app/pdftoolbox/
Email: support@verypdf.com

Usage: pdftoolbox <input files> [options] <-outfile output >

<input files>: a list of input PDF file names.
               Each input file name can occur with a handle which is useful
               when specify page ranges or encrypt PDF. Handles are capital
               letters, e.g., A=in1.pdf, B=in2.pdf.

-outfile     : specify an output file name.

==============PDF Operation Options=======================
-merge           : merge multiple PDF files into one PDF file. You can use
                   handles and handle arguments to specify page ranges,
                   rotate pages, change order when merge PDF.
             odd : the odd-numbered PDF pages, e.g., Aodd is to take odd
                   pages in file A.
             even: the even-numbered PDF pages.
             end : the last page of a file, e.g., A1-end is the same as A.
              E  : rotate 90 degrees, e.g., A4-9E is to rotate the pages 4-9
                   of file A by 90 degrees.
              S  : rotate 180 degrees.
              W  : rotate 270 degrees.
              N  : rotate 0 degree.
              L  : rotate counterclockwise.
              R  : rotate clockwise.
-crossmerge      : the same as -merge except that -crossmerge takes one page
                   at a time from each input PDF file.
-split           : split a multi-page PDF file into single-page PDF files.
                   When split PDF, you can add suffix like _%04d to the end
                   of the specified output file name so that numbers like
                   0001 can be added to the result file names.
-createfdf       : input a single PDF and generate a FDF file suitable for
                   -fillform.
-fillform        : fill form fields of a single input PDF file with the data
                   from an FDF/XFDF file. The form fields remain interactive
                   in the result PDF.
-flattenform     : convert fillable PDF forms to static PDF file.
-underlay        : apply the first page of the background PDF to the
                   background of the single input PDF.
-mulunderlay     : apply each page of the background PDF to the background of
                   the corresponding page of the single input PDF.
-overlay         : use the first page of the background PDF as a watermark
                   and put it over the input PDF.
-muloverlay      : put each page of the background PDF over the corresponding
                   page of the input PDF.
-getinfo         : extract statistics, metadata, bookmarks and page labels
                   from input PDF file to the given output file.
-getinfoutf8     : same as -getinfo except that the output is encoded as
                   UTF-8.
-outformdata     : extract field statistics from the input PDF to the given
                   output file.
-outformdatautf8 : same as -outformdata except that the output is encoded as
                   UTF-8.
-setinfo         : set metadata to PDF's Info dictionary.
-setinfoutf8     : set UTF-8 metadata to PDF's Info dictionary.
-attachfile      : pack arbitrary files into a PDF using PDF's file
                   attachment features.
-detachfile      : copy all the attachments from the input PDF into the
                   current folder or to an output directory given after
                   output.
-pack            : compress stream objects in a PDF file.
-unpack          : uncompress stream objects in a PDF file.
-removexfa       : remove /XFA tag from PDF file.
-showinfo        : show information after processing.
-silent          : do NOT show any information during processing.
-prompt          : prompt information during processing.
-inputpassword   : remove owner password when merge or decrypt PDF.

============= PDF Encryption Options==========================
-key40bit               : set output PDF encryption strength as 40 bits.
-key128bit              : set output PDF encryption strength as 128 bits.
-permit <permissions>   : permissions are applied to the output PDF only if
                          encryption strength is specified or an owner or
                          user password is given.
     printing           : allow top quality printing.
     lowprinting        : allow lower quality printing.
     modifycontents     : allow modifying contents.
     assembly           : allow document assembly.
     copying            : allow copying.
     screenreader       : allow screenreader.
     modifyannot        : allow adding annotation.
     filling            : allow filling interactive PDF form.
     allowall           : allow all the above permissions and top quality
                          printing.
-ownerpassword          : set owner password to output PDF file.
-userpassword           : set user password to output PDF file.
-$ <regcode>            : register with a registration code.

Examples:
Collate scanned pages:
pdftoolbox A=even.pdf B=odd.pdf -crossmerge A B -outfile collated.pdf
or if odd.pdf is in reverse order:
pdftoolbox A=even.pdf B=odd.pdf -crossmerge A Bend-1 -outfile collated.pdf

Decrypt a PDF:
pdftoolbox secured.pdf -inputpassword foopass -outfile unsecured.pdf

Encrypt a PDF using 128-bit strength:
pdftoolbox 1.pdf -outfile 1.128.pdf -ownerpassword foopass

Set an owner password and an user password to a PDF file:
pdftoolbox 1.pdf -outfile out.pdf -ownerpassword opwd -userpassword upwd

Enable high quality printing when encrypt a PDF file:
pdftoolbox 1.pdf -outfile out.pdf -ownerpassword opwd -userpassword upwd
 -permit printing

Merge PDF files into a new PDF:
pdftoolbox in1.pdf in2.pdf -merge -outfile out1.pdf
or (using handles):
pdftoolbox A=in1.pdf B=in2.pdf -merge A B -outfile out1.pdf
or (using wildcards):
pdftoolbox *.pdf -merge -outfile combined.pdf

Remove some page from an input PDF file. The example shows how to remove P13
from the input file:
pdftoolbox in.pdf -merge 1-12 14-end -outfile out1.pdf
or
pdftoolbox A=in1.pdf -merge A1-12 A14-end -outfile out1.pdf

Merge PDF files and add a password for the output file:
pdftoolbox 1.pdf 2.pdf -merge -outfile 3.pdf -key40bit -ownerpassword foopass

Merge PDF files. When one of them requires password, input it:
pdftoolbox A=secured.pdf 2.pdf -inputpassword A=foopass -merge -outfile 3.pdf

Unpack PDF page streams for editing PDF in a text editor:
pdftoolbox doc.pdf -outfile doc.unc.pdf -unpack

Repair PDF's corrupted XREF table and stream lengths:
pdftoolbox broken.pdf -outfile fixed.pdf

Split a multip-page PDF file into single-page PDF files:
pdftoolbox in.pdf -split
pdftoolbox in.pdf -split -outfile pg_4202794.pdf
pdftoolbox in.pdf -split -outfile out_%02d.pdf
pdftoolbox in.pdf -split -outfile out_%04d.pdf

Blast a multip-page PDF file into several encrypted single-page PDF files,
denying low-quality printing:
pdftoolbox in.pdf -split -ownerpassword foopass -permit lowprinting

Extract meta info from input PDF file to the given output file:
pdftoolbox in.pdf -getinfo -outfile report.txt

Rotate the first PDF page clockwise:
pdftoolbox in.pdf -merge 1R 2-end -outfile out.pdf
or
pdftoolbox in.pdf -merge 1E 2-end -outfile out.pdf

Rotate an entire PDF document to 180 degrees:
pdftoolbox in.pdf -merge 1-endS -outfile out.pdf

Add information from text file to output PDF file:
pdftoolbox in.pdf -setinfo in.txt -outfile out.pdf

Add background(s):
pdftoolbox in1.pdf -underlay in2.pdf -outfile out.pdf
pdftoolbox in1.pdf -mulunderlay in2.pdf -outfile out.pdf

Add watermark(s):
pdftoolbox in1.pdf -overlay in2.pdf -outfile out.pdf
pdftoolbox in1.pdf -muloverlay in2.pdf -outfile out.pdf