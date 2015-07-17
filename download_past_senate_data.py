from requests import session
from bs4 import BeautifulSoup
from time import sleep
import re

with session() as r_sesh:

	response = r_sesh.get('http://www.senate.mo.gov/BTSPortal/')

	soup = BeautifulSoup(response.content, 'lxml')

	for a in soup.find(id = 'Accordion1').find_all('a'):

		link = a['href']

		year = int(re.search('\d{4}', link).group())

		file_name = re.search('\w+\.txt', link).group()

		print '   Downloading {0} {1}...'.format(year, file_name)

		sleep(2)

		response = r_sesh.get(link)

		with open('csvs/S_{0}_{1}'.format(year, file_name), 'w') as out_file:
			out_file.write(response.content)

print 'fin.'


