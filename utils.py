from requests import session
from bs4 import BeautifulSoup
import re
from urlparse import urlparse, urlunparse
from time import sleep
from models import *

def get_content(source_page_obj, request_session = None):
	"""Returns content of source_page_obj. If the content wasn't previously downloaded, it requests the content and downloads it."""

	try:
		with open(source_page_obj.file_name, 'r') as f:
			content = f.read()
	except:
		sleep(3)		
		response = request_session.get(source_page_obj.url)
		content = response.content

		with open(source_page_obj.file_name, 'w') as f:
			f.write(content)
	
	return content


def extract_links(content, base_url):
	"""Returns a list of extracted links as dicts from the provided html."""

	out_links = []

	soup = BeautifulSoup(content, 'lxml')

	if 'senate' in base_url:
		chamber = 'S'
		try:
			found_links = soup.find(id = 'list').find_all('a')
		except: # might need to be more explicit
			found_links = soup.find('body').find_all('a')
	elif 'house' in base_url:
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
			out_links.append({
							  'scheme': urlparse(base_url).scheme
							, 'netloc': urlparse(base_url).netloc
							, 'path': urlparse(link['href']).path.replace('./', '/')
							, 'params': urlparse(link['href']).params
							, 'query': urlparse(link['href']).query
							, 'fragment': urlparse(link['href']).fragment
							, 'url': urlunparse((
									  urlparse(base_url).scheme
									, urlparse(base_url).netloc
									, urlparse(link['href']).path.replace('./', '/')
									, urlparse(link['href']).params
									, urlparse(link['href']).query
									, urlparse(link['href']).fragment
								))
							, 'name': link.text
							, 'chamber': chamber
						})
	return out_links