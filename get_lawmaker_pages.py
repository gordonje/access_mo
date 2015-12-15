#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import requests
from models import *
from model_helpers import get_or_create_person, normalize_name_fields, parse_name, get_party
from utils import *
import re
import inspect

name_suffixes = ['II', 'III', 'IV', 'Jr.', 'Jr', 'Sr.', 'Sr']

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
			
			directory = members_list_page.file_name.split('/')
			del directory[-1]
			directory.append('members')

			directory = '/'.join(directory)
			
			if not os.path.exists(directory):
				os.makedirs(directory)

			# get the content of the member list page
			content = None

			while content == None:
				try:
					content = get_content(members_list_page, requests_session)
				except requests.exceptions.ConnectionError as e:
					print e
					print '   Connection failed. Retrying...'
					requests_session = requests.session()

			# place to hold all the members collected from the given member list page
			members = []

			soup = BeautifulSoup(content, 'html5lib')

			# here begins a lot of session and year specific logic for parsing the html
			# first, deal with the house
			if members_list_page.chamber.id == 'H':

				if session.year > 2010:

					for tr in soup.find(id = 'ContentPlaceHolder1_gridMembers_DXMainTable').find_all('tr')[1:]:

						tds = tr.find_all('td')

						last = tds[0].text.strip()
						first_middle = tds[1].text.strip()

						member = {
							  'district': tds[2].text.strip()
							, 'assembly': session.assembly
							, 'chamber': members_list_page.chamber
							, 'raw_name': '{0} {1}'.format(first_middle, last)
							, 'name_dict': {}	
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
							except Exception as e:
								if 'duplicate' in e.message:
									pass
								else:
									print e
									print 'Line #{0}'.format(inspect.currentframe().f_lineno)									
						else:

							# see if there's a suffix in the the last name field
							for suffix in name_suffixes:
								if suffix in last:
									# if so, store this separately, and remove it from the last name
									member['suffix'] = suffix
									last = last.replace(suffix, '').strip()

							member['name_dict']['last_name'] = last

							first_middle_dict = re.match("^(?P<first_name>[\w'\.]+)(?: (?P<middle_name>[\w\.]+))?$", first_middle).groupdict()

							# merge the parsed values into the member dict
							member['name_dict'].update(first_middle_dict)

							member['name_dict'] = normalize_name_fields(member['name_dict'])

							member['party'] = get_party(tds[3].text.strip())
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
						except (AttributeError, KeyError, TypeError, IndexError):
							pass
						except Exception as e:
							print type(e)
							print e.message
							print e.args
							print e

						else:
							d_p = tds[1].text.split('-')
							member = {
								  'district': d_p[0].strip()
								, 'assembly': session.assembly
								, 'chamber': members_list_page.chamber
								, 'raw_name': tds[0].text.strip()
								, 'name_dict': {}
							}
							
							if 'Vacant' in member['raw_name']:
								try:
									with db.atomic():
										District_Vacancy.create(
												  district = member['district']
												, session = session.id
												, chamber = member['chamber']
											)
								except Exception as e:
									if 'duplicate' in e.message:
										pass
									else:
										print e
										print 'Line #{0}'.format(inspect.currentframe().f_lineno)

							else:
								# parse the member's raw name, save the results to the name_dict

								member['name_dict'].update(parse_name(member['raw_name'])['name_dict'])

								member['party'] = get_party(d_p[1].strip())
								
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

				if session.year > 2004:
					# for the post-2004 years, there's a table of members with a 0 border and a width of either 60 or 90 %
					for tr in soup.find('table', attrs = {'border': 0, 'width': re.compile('[6,9]0%')}).find('tbody').find_all('tr'):
						tds = tr.find_all('td')

						# ignore table rows without more than 1 field:
						if len(tds) < 2:
							pass
						# also ignore rows where there first field is missing a link tag
						elif tds[0].find('a') == None:
							pass
						else:
							p_d = tds[1].text.strip().split('-')
							member = {
								  'assembly': session.assembly
								, 'chamber': members_list_page.chamber
								, 'raw_name': tds[0].text.strip()
								, 'name_dict': {}
							}

							if 'Vacant' in member['raw_name']:
								# Some times the vacant district number shows up in the name
								if len(p_d) == 0:
									member['district'] = re.search('\d+', member['raw_name']).group()
								else:
									member['district'] = tds[1].text.strip()
								try:
									with db.atomic():
										District_Vacancy.create(
												  district = member['district']
												, session = session.id
												, chamber = member['chamber']
											)
								except Exception as e:
									if 'duplicate' in e.message:
										pass
									else:
										print e
										print 'Line #{0}'.format(inspect.currentframe().f_lineno)
							else:
								# parse the member's raw name, save the results to the name_dict
								member['name_dict'].update(parse_name(member['raw_name'])['name_dict'])

								member['party'] = get_party(p_d[0])
								member['district'] = p_d[1]
								member['url'] = tds[0].find('a')['href']

								members.append(member)

				elif 2000 < session.year <= 2004:

					for link in soup.find_all('a'):
						# ignore links that are not in a table
						if link.find_parent('td'):

							p_d = link.find_parent('td').find_next_sibling('td').text.strip().split('-')
							member = {
								  'assembly': session.assembly
								, 'chamber': members_list_page.chamber
								, 'raw_name': link.text.strip().replace(',', '')
								, 'name_dict': {}
							}

							if 'Vacant' in member['raw_name']:
								if len(p_d[0]) == 0:
									member['district'] = re.search('\d+', member['raw_name']).group()
								else:
									member['district'] = p_d[0]
								try:
									with db.atomic():
										District_Vacancy.create(
												  district = member['district']
												, session = session.id
												, chamber = member['chamber']
											)
								except Exception as e:
									if 'duplicate' in e.message:
										pass
									else:
										print e
										print 'Line #{0}'.format(inspect.currentframe().f_lineno)
							else:
								# parse the member's raw name, save the results to the name_dict
								member['name_dict'].update(parse_name(member['raw_name'])['name_dict'])

								member['party'] = get_party(p_d[0])
								member['district'] = p_d[1]
								member['url'] = link['href']

								members.append(member)
				else:

					for link in soup.find_all('a'):

						if '/index' not in link['href']:

							member = {
								  'district': re.search('mem(\d+).htm', link['href']).group(1)
								, 'assembly': session.assembly
								, 'chamber': members_list_page.chamber
								, 'raw_name': link.text.replace('Senator', '').replace('\r\n', ' ').strip()
								, 'name_dict': {}
							}

							if 'Vacant' in member['raw_name']:
								try:
									with db.atomic():
										District_Vacancy.create(
												  district = member['district']
												, session = session.id
												, chamber = member['chamber']
											)
								except Exception as e:
									if 'duplicate' in e.message:
										pass
									else:
										print e
										print 'Line #{0}'.format(inspect.currentframe().f_lineno)
							else:
								# parse the member's raw name, save the results to the name_dict
								member['name_dict'].update(parse_name(member['raw_name'])['name_dict'])
							
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
				# get the assembly member's record
				# set up the default query
				member_query = (Assembly_Member
									.select()
									.join(Person)
									.where(
										  (Person.last_name == member['name_dict']['last_name'])
										& (Assembly_Member.district == member['district'])
										& (Assembly_Member.chamber == member['chamber'])
										& (Assembly_Member.assembly == member['assembly'])
									)
								)			
				match_count = member_query.count()
				# if there's only one match on last_name, district, chamber and assembly...
				if match_count == 1:
					# then use that record
					a_m = member_query.get()
				# if there's more than one match...
				elif match_count > 1:
					# add the first initial to the query
					member_query = (Assembly_Member
										.select()
										.join(Person)
										.where(
											  (Person.last_name == member['name_dict']['last_name'])
											& (Person.first_name.startswith(member['name_dict']['first_name'][0]))
											& (Assembly_Member.district == member['district'])
											& (Assembly_Member.chamber == member['chamber'])
											& (Assembly_Member.assembly == member['assembly'])
										)
									)
					# now if there's only one...
					if member_query.count() == 1:
						# then get that one record
						a_m = member_query.get()
					else:
						print 'UNRECONCILED DUPLICATE!'
				# if there aren't any matches...
				elif match_count == 0:
					# try alternate names
					person_names = (Person_Name
										.select(Person.id)
										.join(Person)
										.where(
											  (Person_Name.first_name == member['name_dict']['first_name'])
											& (Person_Name.last_name == member['name_dict']['last_name'])
										)
									)

					member_query = (Assembly_Member
										.select()
										.where(
											  (Assembly_Member.person << person_names)
											& (Assembly_Member.district == member['district'])
											& (Assembly_Member.chamber == member['chamber'])
											& (Assembly_Member.assembly == member['assembly'])
										)
									)
					if member_query.count() == 1:
						a_m = member_query.get()
					else:
						# if we can't find an existing member...

						# then, get or create a person record
						person_select = get_or_create_person(member['name_dict'])

						# if we made a new person, then we need to make a new member record
						if person_select['new_person'] == True:
							print '        Creating new assembly {0} member record for {1}'.format(member['assembly'].id, member['raw_name'])
							with db.atomic():
								a_m = Assembly_Member.create(person = person_select['person'], **member)
						else:
							# if it isn't a new person, try to select a member record for the found person
							try:
								a_m = (Assembly_Member
										.select()
										.where(
											  (Assembly_Member.district == member['district'])
											& (Assembly_Member.assembly == member['assembly'])
											& (Assembly_Member.chamber == member['chamber'])
											& (Assembly_Member.person == person_select['person'])
										)
									).get()
							except Assembly_Member.DoesNotExist:
								# if we can't find one, make a new member record
								print '        Creating new assembly {0} member record for {1}'.format(member['assembly'].id, member['raw_name'])
								with db.atomic():
									a_m = Assembly_Member.create(person = person_select['person'], **member)

				# then, set up the member's session
				profile = Member_Session_Profile(
						  assembly_member = a_m
						, session = session
						, **member
					)

				# then, create or get the source doc
				try:
					with db.atomic():
						profile.source_doc = Source_Doc.create(
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
									, name = '{0} {1}'.format(member['name_dict']['first_name'], member['name_dict']['last_name'])
									, file_name = '{0}/{1}_{2}.html'.format(directory, member['name_dict']['last_name'], member['district'])
									, parent = members_list_page.id
									, session = session.id
						)
				except Exception as e:
					if 'duplicate' in e.message:
						profile.source_doc = Source_Doc.select(
								).where(
									  Source_Doc.file_name == '{0}/{1}_{2}.html'.format(directory, member['name_dict']['last_name'], member['district'])
									, Source_Doc.url == urlunparse((
											  urlparse(members_list_page.url).scheme
											, urlparse(members_list_page.url).netloc
											, urlparse(member['url']).path
											, urlparse(member['url']).params
											, urlparse(member['url']).query
											, urlparse(member['url']).fragment
										))
							   ).get()
					else:
						print e
						print 'Line #{0}'.format(inspect.currentframe().f_lineno)

				# save the session profile
				with db.atomic():
					try:
						profile.save()
					except Exception as e:
						if 'duplicate' in e.message:
							pass
						else:
							print e
							print 'Line #{0}'.format(inspect.currentframe().f_lineno)

				# then, if necessary, download the member's page content
				content = None

				while content == None:
					try:
						content = get_content(profile.source_doc, requests_session)
					except requests.exceptions.ConnectionError as e:
						print e
						print '   Connection failed. Retrying...'
						requests_session = requests.session()
					except Exception as e:
						print e

print 'fin.'

