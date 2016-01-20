
for f in source_docs/SoS/election_results/pdfs/*; do pdftotext -enc UTF-8 -layout $f; done