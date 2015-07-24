import os
import requests
from utils import *

parent = Source_Page.alias()

for bill_page in Source_Page.select(
								Source_Page, parent
							).join(
								parent, on=(Source_Page.parent_id == parent.id).alias('parent')
							).where(
								fn.lower(Source_Page.url).contains('billist') |
								fn.lower(Source_Page.url).contains('billlist')
						    ).order_by(
						    	Source_Page.chamber.desc(), Source_Page.year.desc()
						    ):

	print '   Getting bill links for {0} {1} {2}...'.format(bill_page.chamber, bill_page.year, bill_page.parent.name)
	directory = 'past_content/{0}/{1}_{2}/bills'.format(bill_page.chamber, bill_page.year, bill_page.parent.name.replace(' ', '_')) 

	if not os.path.exists(directory):
		os.makedirs(directory)

	with requests.session() as r_sesh:

		content = None

		while content == None:
			try:
				content = get_content(bill_page, r_sesh)
			except requests.exceptions.ConnectionError, e:
				print e
				print '   Connection failed. Retrying...'
				r_sesh = requests.session()
			except Exception, e:
				print 'Whaa happen?'
				print e

		for link in extract_links(content, bill_page.url):

			name = re.sub('\s{2,}', ' ', link['name']).strip()

			if re.match('\D+_\d+', name):

				link['name'] = name
				link['year'] = bill_page.year
				link['parent_id'] = bill_page.id
				link['file_name'] = '{0}{1}.html'.format(directory, link['name'].replace(' ', '_'))

				try:
					with db.atomic():
						new_page = Source_Page.create(**link)
				except:
					pass
				else:
					content = None

					while content == None:
						try:
							content = get_content(new_page, r_sesh)
						except requests.exceptions.ConnectionError, e:
							print e
							print '   Connection failed. Retrying...'
							r_sesh = requests.session()
						except Exception, e:
							print 'Whaa happen?'
							print e

print 'fin.'