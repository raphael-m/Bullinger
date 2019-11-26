#Rotate the first PDF page to 90 degrees clockwise
../bin/pdftoolbox sample_in1.pdf -merge 1E 2-end -outfile _rotate_first_page_90_out.pdf

#Rotate an entire PDF document to 180 degrees
../bin/pdftoolbox sample_in1.pdf -merge 1-endS -outfile _rotate_all_pages_180_out.pdf

#rotate entire document 90 degrees
		 
../bin/pdftoolbox sample_in1.pdf -merge 1-endE -outfile _rotate_all_pages_90_out.pdf
