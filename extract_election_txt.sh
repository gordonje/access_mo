
for f in past_content/SoS/election_results/pdfs/*; do pdftotext -enc UTF-8 -layout $f; done