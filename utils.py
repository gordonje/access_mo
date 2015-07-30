#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import re
from urlparse import urlparse, urlunparse
from time import sleep

def get_content(source_doc_obj, request_session):
	""" Returns content of source_doc_obj.
		If the content wasn't previously downloaded, it requests the content and downloads it. """

	try:
		with open(source_doc_obj.file_name, 'r') as f:
			content = f.read()
	except:
		print '   No file found. Downloading...'
		sleep(3)
		response = request_session.get(source_doc_obj.url)
		content = response.content

		with open(source_doc_obj.file_name, 'w') as f:
			f.write(content)
	
	return content


def extract_links(content, parent_url):
	""" Returns a list of extracted links as dicts from the provided html. """

	out_links = []

	soup = BeautifulSoup(content, 'lxml')

	if 'senate' in parent_url.lower():
		chamber = 'S'
		try:
			found_links = soup.find(id = 'list').find_all('a')
		except: # might need to be more explicit
			found_links = soup.find('body').find_all('a')
	elif 'house' in parent_url.lower():
		chamber = 'H'
		try:
			found_links = soup.find(attrs = {'style': 'width:700px', 'class': 'sitebox'}).find_all('a')
		except:
			try:
				found_links = soup.find(id = 'right').find_all('a')
			except:
				found_links = soup.find('body').find_all('a')

	for link in found_links:
		if link['href'] != '/':

			parent_path = ''.join(re.findall('.+\/', urlparse(parent_url).path))

			link_path = urlparse(link['href']).path.replace('./', '/') 

			if parent_path not in link_path:
				full_path = parent_path + link_path
			else:
				full_path = link_path

			out_links.append({
							  'scheme': urlparse(parent_url).scheme
							, 'netloc': urlparse(parent_url).netloc
							, 'path': link_path
							, 'params': urlparse(link['href']).params
							, 'query': urlparse(link['href']).query
							, 'fragment': urlparse(link['href']).fragment
							, 'url': urlunparse((
									  urlparse(parent_url).scheme
									, urlparse(parent_url).netloc
									, full_path
									, urlparse(link['href']).params
									, urlparse(link['href']).query
									, urlparse(link['href']).fragment
								))
							, 'name': link.text
							, 'chamber': chamber
						})

	return out_links

