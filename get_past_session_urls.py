#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import requests
from utils import *
from models import *

def get_or_create_session(assembly, year, session_type, name, year_type_num = None):
	""" Returns a session object from the database.
		If there isn't already one in the database, creates a new one.
		The year_type_num arg is really only relevant to extraordinary sessions. """
	if session_type == 'R':
		try:
			with db.atomic():
				sess = Session.create(
					  assembly = assembly
					, year = year
					, session_type = session_type
					, name = name
				)
		except IntegrityError:
			sess = Session.get(
				  assembly = assembly
				, year = year
				, session_type = session_type
			)
	elif session_type == 'E':
		try:
			with db.atomic():
				sess = Session.create(
					  assembly = assembly
					, year = year
					, session_type = session_type
					, name = name
					, year_type_num = year_type_num
				)
		except IntegrityError:
			sess = Session.get(
				  assembly = assembly
				, year = year
				, session_type = session_type
				, year_type_num = year_type_num
			)

	return sess

# set up directories, if necessary
if not os.path.exists('past_content/'):
	os.makedirs('past_content/')

if not os.path.exists('past_content/H/'):
	os.makedirs('past_content/H/')

if not os.path.exists('past_content/S/'):
	os.makedirs('past_content/S/')

# set up a requests session
with requests.session() as requests_session:

	# for each chamber's past session url...
	for chamber in Source_Doc.select().where(Source_Doc.parent >> None
									 ).order_by(Source_Doc.chamber.desc()):

		# request the page containing the list of past sessions
		response = requests_session.get(chamber.url)

		# for each link extracted from the page...
		for link in extract_links(response.content, chamber.url):
			
		# first, set up the legislative session
			sess_data = {
				  'year': int(re.search("\d{4}", link['name']).group())
				, 'name': link['name'].replace('- ', '').strip()
			}

			# assemblies last two years and end on even-numbered years
			if sess_data['year'] % 2 == 0:
				sess_data['assembly'] = Assembly.get(Assembly.end_year == sess_data['year'])
			else:
				sess_data['assembly'] = Assembly.get(Assembly.start_year == sess_data['year'])

			if 'Extraordinary' in link['name']:
				sess_data['session_type'] = 'E'
				# # extraordinary sessions need the year added to the name
				# # and there can be more than one extraordinary session in the same year
				# sess_data['name'] = '{0} {1}'.format(sess_data['year'], sess_data['name'].replace('- ', ''))
				# this is a total hack and will only work as long as there are one or two extraordinary sessions
				if '2nd' in link['name'] or 'Second' in link['name']:
					sess_data['year_type_num'] = 2
				else:
					sess_data['year_type_num'] = 1
			else:
				sess_data['session_type'] = 'R'

			# create the legislative session, or get the id of an exising one
			link['session'] = get_or_create_session(**sess_data).id

		# then, set up the source doc 
			link['parent'] = chamber.id
			link['name'] = sess_data['name']
			link['file_name'] = 'past_content/{0}/{1}.html'.format(
									  link['chamber']
									, sess_data['name']).replace(' ', '_')

			# create the source doc in the db
			Source_Doc.create_or_get(**link)

		# then, for each session page of each chamber, request the session page and get the urls
		for session_page in chamber.children:

			print '    Getting urls for {0} {1}...'.format(
					  session_page.chamber.id
					, session_page.name
				)

			content = None
			# get the past session page content
			while content == None:
				try:
					content = get_content(session_page, requests_session)
				except requests.exceptions.ConnectionError, e:
					print e
					print '   Connection failed. Retrying...'
					requests_session = requests.session()
				except Exception, e:
					print e

			# set up a diretory for each session, if necessary
			directory = 'past_content/{0}/{1}/'.format(
					  session_page.chamber.id
					, session_page.name.replace('.html', '').replace(' ', '_')
				)

			if not os.path.exists(directory):
				os.makedirs(directory)

			# for each on the past session page...
			for link in extract_links(content, session_page.url):

				name = re.sub('\s{2,}', ' ', link['name']).strip()

		# 		ignore links without any text (e.g., images to return to homepage)
				if len(name) > 0:

					link['name'] = name
					link['session'] = session_page.session.id
					link['parent'] = session_page.id
					link['file_name'] = 'past_content/{0}/{1}/{2}.html'.format(
							  session_page.chamber.id
							, session_page.name.replace(' ', '_')
							, link['name'].replace(' ', '_')
						)

					Source_Doc.create_or_get(**link)

print 'fin.'
	