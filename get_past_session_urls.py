import os
from utils import *

if not os.path.exists('past_content/'):
	os.makedirs('past_content/')

if not os.path.exists('past_content/H/'):
	os.makedirs('past_content/H/')

if not os.path.exists('past_content/S/'):
	os.makedirs('past_content/S/')

with session() as r_sesh:

	for chamber in Chamber.select():

		response = r_sesh.get(chamber.past_sessions_url)

		for link in extract_links(response.content, chamber.past_sessions_url):
			
			link['year'] = re.search("\d{4}", link['name']).group()
			link['name'] = re.sub("\d{4}", "", link['name']).lstrip(' - ').strip()
			link['file_name'] = 'past_content/{0}/{1}_{2}.html'.format(link['chamber'], link['year'], link['name'].replace(' ', '_'))

			try:
				with db.atomic():
					Source_Page.create(**link)
			except IntegrityError:
				pass
				
	# go through each session

	for sess_page in Source_Page.select(
							   ).where(Source_Page.parent_id == 0 
							   ).order_by(
							   		Source_Page.chamber
							   	  , Source_Page.year.desc()
							   ):

		# create a new session, if necessary

		# going to use the senate as the authoritative list of sessions
		if sess_page.chamber == 'S':
		# even numbered years are the second of assemblies, odd years are the first of assemblies

			if 'Extraordinary' in sess_page.name:
				session_type = 'E'
			else:
				session_type = 'R'

			if sess_page.year % 2 == 0:
				assembly = Assembly.get(Assembly.end_year == sess_page.year)
			else:
				assembly = Assembly.get(Assembly.start_year == sess_page.year)

			Session.get_or_create(
				  assembly = assembly
				, year = sess_page.year
				, session_type = session_type
				, name = sess_page.name
			)

		# now collect all the urls within the session page

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

		# there's an additional 2001 extraordinary session that the senate is missing
		# house page is http://house.mo.gov/billtracking/spec01/billist.htm
		# senate page is http://www.senate.mo.gov/01info/sp/bil-list.htm

		Session.get_or_create(assembly = 91, session_type = 'E', name = '2001 Extraordinary Session', year = 2001)

print 'fin.'