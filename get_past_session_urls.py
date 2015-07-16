import os
from utils import *

cham_urls = [
	  'http://www.house.mo.gov/sitemap.aspx?pid=24'
	, 'http://www.senate.mo.gov/pastsessions.htm'
]

if not os.path.exists('past_content/'):
	os.makedirs('past_content/')

if not os.path.exists('past_content/H/'):
	os.makedirs('past_content/H/')

if not os.path.exists('past_content/S/'):
	os.makedirs('past_content/S/')

with session() as r_sesh:

	for cham_url in cham_urls:

		response = r_sesh.get(cham_url)

		for link in extract_links(response.content, cham_url):
			
			link['year'] = re.search("\d{4}", link['name']).group()
			link['name'] = re.sub("\d{4}", "", link['name']).lstrip(' - ').strip()
			link['file_name'] = 'past_content/{0}/{1}_{2}.html'.format(link['chamber'], link['year'], link['name'].replace(' ', '_'))

			try:
				with db.atomic():
					Source_Page.create(**link)
			except IntegrityError:
				pass
				
	# collect the urls from within each session

	for sess_page in Source_Page.select().where(Source_Page.parent_id == 0).order_by(Source_Page.chamber, Source_Page.year.desc()):
		print 'Getting urls for {0} {1} {2}...'.format(sess_page.chamber, sess_page.year, sess_page.name)

		directory = 'past_content/{0}/{1}_{2}/'.format(sess_page.chamber, sess_page.year, sess_page.name.replace(' ', '_'))

		if not os.path.exists(directory):
			os.makedirs(directory)

		try:
			content = get_content(sess_page, r_sesh)
		except: # needs to be more specific
			r_sesh = session()
			content = get_content(sess_page, r_sesh)

		for link in extract_links(content, sess_page.url):

			name = re.sub('\s{2,}', ' ', link['name']).strip()

			if len(name) > 0:

				link['name'] = name
				link['year'] = sess_page.year
				link['parent_id'] = sess_page.id
				link['file_name'] = 'past_content/{0}/{1}_{2}/{3}.html'.format(sess_page.chamber, sess_page.year, sess_page.name.replace(' ', '_'), link['name'].replace(' ', '_'))

				try:
					with db.atomic():
						Source_Page.create(**link)
				except IntegrityError:
					pass

print 'fin.'