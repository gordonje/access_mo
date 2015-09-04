#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import inspect
import re
import requests

from cStringIO import StringIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

def convert(fname, pages=None):
    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)

    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)

    infile = file(fname, 'rb')
    for page in PDFPage.get_pages(infile, pagenums):
        print '====== Page Break ======='
        interpreter.process_page(page)
    infile.close()
    converter.close()
    text = output.getvalue()
    output.close
    return text 

for pdf in os.listdir('past_content/SoS/'):

	print pdf

	print convert('past_content/SoS/' + pdf)


# from pdfminer.pdfparser import PDFParser
# from pdfminer.pdfdocument import PDFDocument
# from pdfminer.pdfpage import PDFPage
# from pdfminer.pdfpage import PDFTextExtractionNotAllowed
# from pdfminer.pdfinterp import PDFResourceManager
# from pdfminer.pdfinterp import PDFPageInterpreter
# from pdfminer.pdfdevice import PDFDevice
# from pdfminer.layout import LAParams
# from pdfminer.converter import PDFPageAggregator

# for pdf in os.listdir('past_content/SoS/'):

# 	print pdf

# 	# Open a PDF file.
# 	fp = open('past_content/SoS/' + pdf, 'rb')
# 	# Create a PDF parser object associated with the file object.
# 	parser = PDFParser(fp)
# 	# Create a PDF document object that stores the document structure.
# 	# Supply the password for initialization.
# 	document = PDFDocument(parser)
# 	# Check if the document allows text extraction. If not, abort.
# 	if not document.is_extractable:
# 	    raise PDFTextExtractionNotAllowed
# 	# Create a PDF resource manager object that stores shared resources.
# 	rsrcmgr = PDFResourceManager()
# 	# Set parameters for analysis.
# 	laparams = LAParams()
# 	# Create a PDF page aggregator object.
# 	device = PDFPageAggregator(rsrcmgr, laparams=laparams)
# 	interpreter = PDFPageInterpreter(rsrcmgr, device)
# 	# Process each page contained in the document.
# 	for page in PDFPage.create_pages(document):
# 		interpreter.process_page(page)
#     	# receive the LTPage object for the page.
#     	layout = device.get_result()
#     	print type(layout)
#     	print dir(layout)
#     	print layout.(laparams)

