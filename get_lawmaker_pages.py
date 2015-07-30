# TO DO: need to check if there are name suffix (e.g., 'Jr.', 'Sr.') to handle

import os
import requests
from models import *
from utils import *

# set up a requests session
with requests.session() as requests_session:

# for each regular legislative session (ignoring extraordinary, since members rarely change for these)...
	for session in Session.select().where(~Session.name.contains('Extraordinary')):

		# get the member list page for each session (one for each chamber)
		for members_list_page in session.source_docs.where(
				Source_Doc.name.contains('Roster') | Source_Doc.name.contains('Senators')):
			print '   Getting members for {0} {1}...'.format(
						  members_list_page.chamber.id
						, session.name
				)
			
			# create a members folder in each session folder, if necessary
			directory = 'past_content/{0}/{1}/members'.format(
						  members_list_page.chamber.id
						, members_list_page.parent.name.replace(' ', '_')
				) 
			
			if not os.path.exists(directory):
				os.makedirs(directory)

			# get the content of the member list page
			content = None

			while content == None:
				try:
					content = get_content(members_list_page, requests_session)
				except requests.exceptions.ConnectionError, e:
					print e
					print '   Connection failed. Retrying...'
					requests_session = requests.session()

			# place to hold all the members collected from the given member list page
			members = []

			# here begins a lot of session and year specific logic for parsing the html
			# first, deal with the house
			if members_list_page.chamber.id == 'H':

				# some parsers work better for certain years, apparently
				if session.year > 2001:
					soup = BeautifulSoup(content, 'lxml')
				elif session.year <= 2001:
					soup = BeautifulSoup(content, 'html5lib')

				if session.year > 2010:

					for tr in soup.find(id = 'ContentPlaceHolder1_gridMembers_DXMainTable').find_all('tr')[1:]:

						tds = tr.find_all('td')

						last = tds[0].text.strip()

						member = {
							  'district': tds[2].text.strip()
							, 'assembly': session.assembly.id
							, 'chamber': members_list_page.chamber.id
						}

						# tracking if the district was vacant during the session
						if last == 'Vacant':
							try:
								with db.atomic():
									District_Vacancy.create(
											  district = member['district']
											, session = session.id
											, chamber = member['chamber']
										)
							except Exception, e:
								print 'Duplicate District_Vacancy'
								print e
						else:
							# if there is a middle name, it's found in second field along with the first name
							member['last'] = last
							first_middle = tds[1].text.strip().split()

							member['first'] = first_middle.pop(0)
							try:
								member['middle'] = first_middle.pop()
							except Exception, e:
								member['middle'] = None

							member['party'] = tds[3].text.strip()
							member['url'] = 'http://house.mo.gov/member.aspx?year={0}&district={1}'.format(session.year, member['district'])

							members.append(member)

				if session.year <= 2010:

					# in 1998, the house decreased the width of the table listing members, but then switched it back
					if session.year == 1998:
						trs = soup.find('table', attrs = {'border': 2, 'width': '80%'}).find_all('tr')
					else:
						trs = soup.find('table', attrs = {'border': 2, 'width': '100%'}).find_all('tr')

					for tr in trs:
						tds = tr.find_all('td')

						# the formatting of some of these tables is INSANE
						# for some reason this check works: look in the first td for a link with a url
						try:
							tds[0].find('a')['href']
						except Exception, e:
							pass
						else:
							name = tds[0].text.strip().split()
							d_p = tds[1].text.split('-')
							member = {
								  'district': d_p[0].strip()
								, 'assembly': session.assembly.id
								, 'chamber': members_list_page.chamber.id
							}
							
							if 'Vacant' in name:
								try:
									with db.atomic():
										District_Vacancy.create(
												  district = member['district']
												, session = session.id
												, chamber = member['chamber']
											)
								except Exception, e:
									print 'Duplicate District_Vacancy'
									print e
							else:
								member['last'] = name.pop(-1)
								member['first'] = name.pop(0)
								try:
									member['middle'] = name.pop()
								except:
									member['middle'] = None
								member['party'] = d_p[1].strip()
								if member['party'] == '':
									member['party'] = None

								# the urls for H 2009 and 2010 are like later years, though everything else is like earlier years
								if session.year in [2009, 2010]:
									member['url'] = 'http://house.mo.gov/member.aspx?year={0}&district={1}'.format(session.year, member['district'])
								else:
									member['url'] = tds[0].find('a')['href']

								members.append(member)

			# now, deal with the senate
			if members_list_page.chamber.id == 'S':

				soup = BeautifulSoup(content, 'lxml')

				if session.year > 2004:
					# for the post-2004 years, there's a table of members with a 0 border and a width of either 60 or 90 %
					for tr in soup.find('table', attrs = {'border': 0, 'width': re.compile('[6,9]0%')}).find_all('tr'):
						tds = tr.find_all('td')

						# ignore table rows without more than 1 field:
						if len(tds) < 2:
							pass
						# also ignore rows where there first field is missing a link tag
						elif tds[0].find('a') == None:
							pass
						else:
							name = tds[0].text.strip().split()
							p_d = tds[1].text.strip().split('-')
							member = {
								  'assembly': session.assembly.id
								, 'chamber': members_list_page.chamber.id
							}

							if 'Vacant' in name:
								# Some times the vacant district number shows up in the name
								if len(p_d) == 0:
									member['district'] = name.pop(-1)
								else:
									member['district'] = tds[1].text.strip()
								try:
									with db.atomic():
										District_Vacancy.create(
												  district = member['district']
												, session = session.id
												, chamber = member['chamber']
											)
								except Exception, e:
									print 'Duplicate District_Vacancy'
									print e
							else:
								member['last'] = name.pop(-1)
								member['first'] = name.pop(0)
								try:
									member['middle'] = name.pop()
								except:
									member['middle'] = None
								member['party'] = p_d[0]
								member['district'] = p_d[1]
								member['url'] = tds[0].find('a')['href']

								members.append(member)

				elif 2000 < session.year <= 2004:

					for link in soup.find_all('a'):
						# ignore links that are not in a table
						if link.find_parent('td'):

							name = link.text.strip().split()
							p_d = link.find_parent('td').find_next_sibling('td').text.strip().split('-')
							member = {
								  'assembly': session.assembly.id
								, 'chamber': members_list_page.chamber.id
							}

							if 'Vacant' in name:
								if len(p_d[0]) == 0:
									member['district'] = name.pop(-1)
								else:
									member['district'] = p_d[0]
								try:
									with db.atomic():
										District_Vacancy.create(
												  district = member['district']
												, session = session.id
												, chamber = member['chamber']
											)
								except Exception, e:
									print e
							else:
								member['last'] = name.pop(-1)
								member['first'] = name.pop(0)
								try:
									member['middle'] = name.pop()
								except:
									member['middle'] = None
								member['party'] = p_d[0]
								member['district'] = p_d[1]
								member['url'] = link['href']

								members.append(member)

				else:

					for link in soup.find_all('a'):

						if '/index' not in link['href']:

							# split the name and remove the title
							name = [ i for i in link.text.strip().split() if not i.startswith('Senator')]

							member = {
								  'district': re.search('mem(\d+).htm', link['href']).group(1)
								, 'assembly': session.assembly.id
								, 'chamber': members_list_page.chamber.id
							}

							if 'Vacant' in name:
								try:
									with db.atomic():
										District_Vacancy.create(
												  district = member['district']
												, session = session.id
												, chamber = member['chamber']
											)
								except Exception, e:
									print e
							else:
								member['last'] = name.pop(-1)
								member['first'] = name.pop(0)
								try:
									member['middle'] = name.pop()
								except:
									member['middle'] = None
								# party cannot be found on these pages
								member['party'] = None

								parent_url_path = re.search('^.+\.gov\/.+\/', members_list_page.url).group()

								if members_list_page.url not in link['href']:
									member['url'] = parent_url_path + link['href']
								else:
									member['url'] = link['href']
						
								members.append(member)

			# now, loop over all the members collected on the page
			for member in members:
				# either create or get the member's source page
				try:
					with db.atomic():
						member['source_doc'] = Source_Doc.create(
									  chamber = member['chamber']
									, scheme = urlparse(members_list_page.url).scheme
									, netloc = urlparse(members_list_page.url).netloc
									, path = urlparse(member['url']).path
									, params = urlparse(member['url']).params
									, query = urlparse(member['url']).query
									, fragment = urlparse(member['url']).fragment
									, url = urlunparse((
											  urlparse(members_list_page.url).scheme
											, urlparse(members_list_page.url).netloc
											, urlparse(member['url']).path
											, urlparse(member['url']).params
											, urlparse(member['url']).query
											, urlparse(member['url']).fragment
										))
									, name = '{0} {1}'.format(member['first'], member['last'])
									, file_name = '{0}/{1}.html'.format(directory, member['district'])
									, parent = members_list_page.id
									, session = session.id
						)
				except Exception, e:
					member['source_doc'] = Source_Doc.get( 
						  file_name = '{0}/{1}.html'.format(directory, member['district'])
						, url = urlunparse((
								  urlparse(members_list_page.url).scheme
								, urlparse(members_list_page.url).netloc
								, urlparse(member['url']).path
								, urlparse(member['url']).params
								, urlparse(member['url']).query
								, urlparse(member['url']).fragment
							))
					)

				# then either create or get a person record
				try:
					with db.atomic():
						member['person'] = Person.create(
										  first_name = member['first']
										, middle_name = member['middle']
										, last_name = member['last']
							)
				except Exception, e:
					member['person'] = Person.get(first_name = member['first'], last_name = member['last'])

				# then try making the member record
				try:
					with db.atomic():
						Assembly_Member.create(**member)
				except Exception, e: # should be more specific
					pass

				# then, if necessary, download the member's page content
				content = None

				while content == None:
					try:
						content = get_content(member['source_doc'], requests_session)
					except requests.exceptions.ConnectionError, e:
						print e
						print '   Connection failed. Retrying...'
						requests_session = requests.session()
					except Exception, e:
						print e


print 'fin.'

