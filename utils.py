#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import re
from urlparse import urlparse, urlunparse
from time import sleep

def get_content(source_doc_obj, requests_session):
	""" Returns content of source_doc_obj.
		If the content wasn't previously downloaded, it requests the content and downloads it. """

	try:
		with open(source_doc_obj.file_name, 'r') as f:
			content = f.read()
	except:
		print '   No file found. Downloading from {}'.format(source_doc_obj.url)
		sleep(3)
		response = requests_session.get(source_doc_obj.url)
		response.raise_for_status()
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
		except AttributeError:
			found_links = soup.find('body').find_all('a')
		except Exception:
			raise

	elif 'house' in parent_url.lower():
		chamber = 'H'
		try:
			found_links = soup.find(attrs = {'style': 'width:700px', 'class': 'sitebox'}).find_all('a')
		except:
			try:
				found_links = soup.find(id = 'right').find_all('a')
			except AttributeError:
				found_links = soup.find('body').find_all('a')
			except Exception:
				raise

	for link in found_links:
		if link['href'] != '/':

			parent_path = ''.join(re.findall('.+\/', urlparse(parent_url).path))

			link_path = urlparse(link['href']).path.replace('./', '/').strip()

			if parent_path.lower() not in link_path.lower():
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

