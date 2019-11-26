../bin/pdftoolbox.exe sample_verypdf.pdf -attachfile sample_in1.pdf sample_in2.pdf sample_fillform.pdf -outfile _attachment.pdf

mkdir _attachment
../bin/pdftoolbox.exe _attachment.pdf -detachfile -outfile _attachment/

#