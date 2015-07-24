import os
import requests
from utils import *

parent = Source_Page.alias()

for bills_list_page in Source_Page.select(
								Source_Page, parent
							).join(
								parent, on=(Source_Page.parent_id == parent.id).alias('parent')
							).where(
								fn.lower(Source_Page.url).contains('billist') |
								fn.lower(Source_Page.url).contains('billlist')
						    ).order_by(
						    	Source_Page.chamber.desc(), Source_Page.year.desc()
						    ):

	print '   Getting bill links for {0} {1} {2}...'.format(
													  bills_list_page.chamber
													, bills_list_page.year
													, bills_list_page.parent.name
												)
	directory = 'past_content/{0}/{1}_{2}/bills'.format(
													  bills_list_page.chamber
													, bills_list_page.year
													, bills_list_page.parent.name.replace(' ', '_')
												) 

	if not os.path.exists(directory):
		os.makedirs(directory)

	with requests.session() as r_sesh:

		content = None

		while content == None:
			try:
				content = get_content(bills_list_page, r_sesh)
			except requests.exceptions.ConnectionError, e:
				print e
				print '   Connection failed. Retrying...'
				r_sesh = requests.session()
			except Exception, e:
				print 'Whaa happen?'
				print e

		for link in extract_links(content, bills_list_page.url):

			name = re.sub('\s{2,}', ' ', link['name']).strip()

			if re.match('\D+\s\d+', name):

				link['name'] = name
				link['year'] = bills_list_page.year
				link['parent_id'] = bills_list_page.id
				link['file_name'] = '{0}/{1}.html'.format(directory, link['name'].replace(' ', '_'))

				try:
					with db.atomic():
						bill_sum_page = Source_Page.get_or_create(**link)[0]
				except Exception, e:
					print e

				content = None

				while content == None:
					try:
						content = get_content(bill_sum_page, r_sesh)
					except requests.exceptions.ConnectionError, e:
						print e
						print '   Connection failed. Retrying...'
						r_sesh = requests.session()
					except Exception, e:
						print 'Whaa happen?'
						print e

				bill_data = {
					  'session': Session.get(name = bills_list_page.parent.name)
					, 'bill_type': link['name'].split()[0]
					, 'number': link['name'].split()[1]
					, 'source_page': bill_sum_page
				}

				try:
					with db.atomic():
						bill = Bill.get_or_create(**bill_data)
				except Exception, e:
					print e


print 'fin.'