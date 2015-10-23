#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import requests
from bs4 import BeautifulSoup
from urlparse import urlparse
import re
from time import sleep
import inspect

f_path = 'past_content/SoS/election_results/pdfs/'

if not os.path.exists(f_path):
	os.makedirs(f_path)

with requests.session() as requests_session:

	response = requests_session.get('http://s1.sos.mo.gov/elections/resultsandstats/previousElections')

	soup = BeautifulSoup(response.content, 'lxml')

	for link in soup.find_all('a'):

		try:
			url = link['href']
		except KeyError:
			pass
		else:
			if '.pdf' in url:
				if 'special' in url.lower() or 'allracesgeneral' in url.lower() or 'primary' in url.lower():
					if 'county' not in url.lower():
						print url
						file_name = f_path + re.search('\/.+\/(.+\.pdf)', urlparse(url).path).group(1).replace(' ', '')
						
						sleep(3)
						response = requests_session.get(url)

						with open(file_name, 'w') as f:
							f.write(response.content)

print 'fin.'
