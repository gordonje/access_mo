#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path, makedirs
import requests
from bs4 import BeautifulSoup
from urlparse import urlparse
import re
from time import sleep
import inspect
from model_helpers import get_or_create_source_doc, Source_Doc

# set up the file path for election pdfs
f_path = 'source_docs/SoS/election_results/pdfs/'
# create it, if necessary
if not path.exists(f_path):
	makedirs(f_path)

# get the source doc for past SoS elections
past_results_page = Source_Doc.get(Source_Doc.url == 'http://s1.sos.mo.gov/elections/resultsandstats/previousElections')

with requests.session() as requests_session:

	# first, get the page that lists all election results pdfs
	response = requests_session.get(past_results_page.url)

	# parse it
	soup = BeautifulSoup(response.content, 'lxml')

	# iterate over all the link tags
	for link in soup.find_all('a'):

		try:
			url = link['href']
		except KeyError:
			pass
		else:
			# make sure the link points to a pdf file
			if '.pdf' in url:
				# make sure the link points to special, general or primary election results
				if 'special' in url.lower() or 'allracesgeneral' in url.lower() or 'primary' in url.lower():
					# don't need county by county results
					if 'county' not in url.lower():

						# set up the file name
						elec_name = re.search('\/.+\/(.+\.pdf)', urlparse(url).path).group(1).strip()
						file_name = f_path + elec_name.replace(' ', '')

						# check to see if we already have the file
						if path.isfile(file_name):
							print "  Already downloaded {}.".format(file_name)
						else:
							print "  Downloading {}.".format(file_name)
						
							# request the pdf
							sleep(3)
							response = requests_session.get(url)

							# save the file
							with open(file_name, 'w') as f:
								f.write(response.content)

						# whether we have the file or not, try creating a source_doc
						doc = get_or_create_source_doc(
								  source = 'SoS'
								, name = elec_name
								, file_name = file_name
								, url = url
								, parent = past_results_page
							)

print 'fin.'
