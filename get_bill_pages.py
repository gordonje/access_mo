import os
from utils import *

parent = Source_Page.alias()

for bill_page in Source_Page.select(
								Source_Page, parent
							).join(
								parent, on=(Source_Page.parent_id == parent.id).alias('parent')
							).where(
								Source_Page.url.contains('billist')| Source_Page.url.contains('billlist')
						    ).order_by(
						    	Source_Page.chamber, Source_Page.year.desc()
						    ):

	print '   Getting bill links for {0} {1} {2}...'.format(bill_page.chamber, bill_page.year, bill_page.parent.name)

	directory = 'past_content/{0}/{1}_{2}/'.format(bill_page.chamber, bill_page.year, bill_page.parent.name.replace(' ', '_')) 

	try:
		content = get_content(bill_page, r_sesh)
	except: # needs to be more specific
		r_sesh = session()
		content = get_content(bill_page, r_sesh)

	for link in extract_links(content, bill_page.url):

		name = re.sub('\s{2,}', ' ', link['name']).strip()

		if re.search('\d+', name):

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
				try:
					get_content(new_page, r_sesh)
				except:
					print '      Lost connection, resetting session...'
					r_sesh = session()
					get_content(new_page, r_sesh)