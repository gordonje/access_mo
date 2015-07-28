#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import requests
from models import *
from utils import *

# set up a requests session
with requests.session() as requests_session:

	for session in Session.select():

		for bills_list_page in session.source_docs.where(
								fn.lower(Source_Doc.url).contains('billist') |
								fn.lower(Source_Doc.url).contains('billlist')
				):

			if bills_list_page.chamber.id == 'H': # remove this line later
				if session.year <= 2010 & session.year != 2008: #remove this line later

					print '   Getting bill links for {0} {1} {2}...'.format(
								  bills_list_page.chamber.id
								, session.year
								, session.name
						)
					directory = 'past_content/{0}/{1}_{2}/bills'.format(
								  bills_list_page.chamber.id
								, session.year
								, bills_list_page.parent.name.replace(' ', '_')
						) 

					if not os.path.exists(directory):
						os.makedirs(directory)

					content = None

					while content == None:
						try:
							content = get_content(bills_list_page, requests_session)
						except requests.exceptions.ConnectionError, e:
							print e
							print '   Connection failed. Retrying...'
							requests_session = requests.session()
						except Exception, e:
							print e

					for link in extract_links(content, bills_list_page.url):

						name = re.sub('\s{2,}', ' ', link['name']).strip()

						if re.match('\D+\s\d+', name):

							link['session'] = session.id
							link['name'] = name
							link['parent'] = bills_list_page.id
							link['file_name'] = '{0}/{1}.html'.format(directory, link['name'].replace(' ', '_'))

							try:
								with db.atomic():
									Source_Doc.create(**link)
							except Exception, e:
								pass

					for bill_details_page in bills_list_page.children:


						bill = Bill(
								  session = session.id
								, chamber = bill_details_page.chamber.id
								, source_doc = bill_details_page
							)

						content = None

						while content == None:
							try:
								content = get_content(bill_details_page, requests_session)
							except requests.exceptions.ConnectionError, e:
								print e
								print '   Connection failed. Retrying...'
								requests_session = requests.session()
							except Exception, e:
								print 'Error happening when getting content'
								print e

						soup = BeautifulSoup(content, 'lxml')

				# if bill_details_page.chamber.id == 'H':

					# if session.year > 2010:

					# 	bill_details = soup.find('div', id = 'BillDetails')

					# 	bill.bill_type = bill_details.find('span', attrs = {'class':'entry-title'}).text.split(' ')[0]
					# 	bill.number = int(bill_details.find('span', attrs = {'class':'entry-title'}).text.split(' ')[1])
					# 	bill.description = bill_details.find('div', attrs = {'class':'BillDescription'}).text.strip('"').strip()

					# 	for tr in bill_details.find('table').findAll('tr'):
					# 		if tr.find('td') != None:

					# 			if tr.find('th').text == 'Sponsor:':

					# 				bill.sponsor_string = tr.find('td').text

					# 				try:
					# 					raw_sponsor = re.search('(.+),\s+([\w|\.]+).*\((\d*)\)', bill.sponsor_string)
					# 					bill.sponsor = Assembly_Member.select(
					# 									   ).join(Person
					# 									   ).where(
					# 											  Person.last_name == raw_sponsor.group(1)
					# 											, Person.first_name == raw_sponsor.group(2)
					# 											# , Assembly_Member.district == raw_sponsor.group(2)
					# 											, Assembly_Member.assembly == session.assembly
					# 											, Assembly_Member.chamber == bill_details_page.chamber
					# 									   ).get()
					# 				except:
					# 					bill.sponsor = None

					# 			if tr.find('th').text == 'LR Number:':
					# 				bill.lr_number = tr.find('td').text

					# 			if tr.find('th').text == 'Proposed Effective Date:':
					# 				bill.effective_date = tr.find('td').text

					# 			if tr.find('th').text == 'Bill String:':
					# 				bill.bill_string = tr.find('td').text

					# 	actions_link = soup.find('div', class_ = 'Sections').find('a')['href']

					# 	try:
					# 		with db.atomic():
					# 			bill.source_doc = Source_Doc.create(
					# 						  chamber = bill_details_page.chamber
					# 						, scheme = urlparse(bill_details_page.url).scheme
					# 						, netloc = urlparse(bill_details_page.url).netloc
					# 						, path = urlparse(actions_link).path
					# 						, params = urlparse(actions_link).params
					# 						, query = urlparse(actions_link).query
					# 						, fragment = urlparse(actions_link).fragment
					# 						, url = urlunparse((
					# 								  urlparse(bill_details_page.url).scheme
					# 								, urlparse(bill_details_page.url).netloc
					# 								, urlparse(actions_link).path
					# 								, urlparse(actions_link).params
					# 								, urlparse(actions_link).query
					# 								, urlparse(actions_link).fragment
					# 							))
					# 						, name = '{0} actions'.format(bill.bill_string)
					# 						, file_name = '{0}_actions.html'.format(bill_details_page.file_name.rstrip('.html'))
					# 						, parent = bill_details_page.id
					# 						, session = session.id
					# 			)
					# 	except Exception, e:
					# 		bill.source_doc = Source_Doc.get( 
					# 			  file_name = '{0}_actions.html'.format(bill_details_page.file_name.rstrip('.html'))
					# 			, url = urlunparse((
					# 					  urlparse(bill_details_page.url).scheme
					# 					, urlparse(bill_details_page.url).netloc
					# 					, urlparse(actions_link).path
					# 					, urlparse(actions_link).params
					# 					, urlparse(actions_link).query
					# 					, urlparse(actions_link).fragment
					# 				))
					# 		)

					# 	content = None

					# 	while content == None:
					# 		try:
					# 			content = get_content(bill.source_doc, requests_session)
					# 		except requests.exceptions.ConnectionError, e:
					# 			print e
					# 			print '   Connection failed. Retrying...'
					# 			sleep(5)
					# 			requests_session = requests.session()
					# 		except Exception, e:
					# 			print e

					# elif session.year <= 2010 & session.year != 2008:

						# bill_details = soup.find('div', class_ = 'sitebox').find('table')

						# bill.bill_type = bill_details.find('td').text.strip().split()[0]
						# bill.number = int(bill_details.find('td').text.strip().split()[1])
						# bill.description = bill_details.find('td').find_next('td').text.strip()

						actions_link = soup.find('center').find('table').find('td').find('a')['href']

						try:
							with db.atomic():
								bill.source_doc = Source_Doc.create(
											  chamber = bill_details_page.chamber
											, scheme = urlparse(bill_details_page.url).scheme
											, netloc = urlparse(bill_details_page.url).netloc
											, path = urlparse(actions_link).path
											, params = urlparse(actions_link).params
											, query = urlparse(actions_link).query
											, fragment = urlparse(actions_link).fragment
											, url = urlunparse((
													  urlparse(bill_details_page.url).scheme
													, urlparse(bill_details_page.url).netloc
													, urlparse(actions_link).path
													, urlparse(actions_link).params
													, urlparse(actions_link).query
													, urlparse(actions_link).fragment
												))
											, name = '{0} actions'.format(bill.bill_string)
											, file_name = '{0}_actions.html'.format(bill_details_page.file_name.rstrip('.html'))
											, parent = bill_details_page.id
											, session = session.id
								)
						except Exception, e:
							bill.source_doc = Source_Doc.get( 
								  file_name = '{0}_actions.html'.format(bill_details_page.file_name.rstrip('.html'))
								, url = urlunparse((
										  urlparse(bill_details_page.url).scheme
										, urlparse(bill_details_page.url).netloc
										, urlparse(actions_link).path
										, urlparse(actions_link).params
										, urlparse(actions_link).query
										, urlparse(actions_link).fragment
									))
							)

						content = None

						while content == None:
							try:
								content = get_content(bill.source_doc, requests_session)
							except requests.exceptions.ConnectionError, e:
								print e
								print '   Connection failed. Retrying...'
								sleep(5)
								requests_session = requests.session()
							except Exception, e:
								print e

						# for k, v in bill._data.iteritems():
						# 	print '{}: {}'.format(k, v)
						# print 'chamber: {}'.format(bill.chamber)
						# # try:
						# # 	print 'sponsor: {}'.format(bill.sponsor.district)
						# # except:
						# # 	print 'sponsor: {}'.format(bill.sponsor)


# 						bill = Bill(
# 								  session = session.id
# 								, chamber = bills_list_page.chamber.id
# 								, bill_type = bill_details.find('span', attrs = {'class':'entry-title'}).text.split(' ')[0]
# 								, number = int(bill_details.find('span', attrs = {'class':'entry-title'}).text.split(' ')[1])
# 								, description = bill_details.find('div', attrs = {'class':'BillDescription'}).text.strip('"').strip()
# 								, source_doc = bill_details_page
# 							)						

# 						# else:

# 							# Figure out what to target before H 2008





# 							# print bill.bill_type.id
# 							# print bill.number
# 							# print '-----------	'




# 					# try:
# 					# 	with db.atomic():
# 					# 		bill = Bill.create(**bill_data)
# 					# except Exception, e:
# 					# 	print 'Error when making bill'
# 					# 	print e
# 					# 	for k, v in bill_data.iteritems():
# 					# 		print '{0}: {1}'.format(k, v)

# print 'fin.'