#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import requests
from models import *
from model_helpers import parse_name
from utils import *
import inspect
import codecs
from datetime import datetime

def parse_journal_pages(tag):
	""" Accepts a BeautifulSoup tag that should contain journal pages.
		Parses the journal page information into objects.
		Returns a list of Bill_Action_Journal_Page objects. 
	"""

	pages = []

	# split it at the '/', meaning that there's both H and S journals
	jour_split = tag.text.split('/')

	for jour in jour_split:

		# indicates the journal entry spans multiple pages
		page_split = jour.split('-')

		# is it a house journal page?
		if re.match('H\s*\d+', jour.strip()):
			page = Bill_Action_Journal_Page(
				  chamber = 'H'
				, start_page = re.search('\d+', page_split.pop(0)).group()
			)
		# or a senate journal page?
		elif re.match('S\s*\d+', jour.strip()):

			page = Bill_Action_Journal_Page(
				  chamber = 'S'
				, start_page = re.search('\d+', page_split.pop(0)).group()
			)

		else:
			# in cases where the 'H' or 'S' prefix is not included, leave the chamber null
			# could perhaps look at the link's domain to fix this later
			page = Bill_Action_Journal_Page(
				start_page = re.search('\d+', page_split.pop(0)).group()
			)

		try:
			# this will fail if the journal entry is only on one page
			page.end_page = re.search('\d+', page_split.pop(-1)).group()
		except (IndexError, AttributeError) as e:
			# in which case the first and last journal page are one-in-the-same
			page.end_page = page.start_page

		try:
			page.journal_link = tag.find('a', text = jour.strip())['href']
		except TypeError:
			page.journal_link = None

		pages.append(page)

	return pages


start_time = datetime.now()

# set up a requests session...
with requests.session() as requests_session:
	# for each legislative session...
	for session in Session.select().order_by(Session.year.desc()):
		# for each bill list page of the session...
		for bills_list_page in session.source_docs.where(
								( (Source_Doc.chamber == 'H') & (
										fn.lower(Source_Doc.url).contains('billist') | 
										fn.lower(Source_Doc.url).contains('billlist')
									) 
								) |
								( (Source_Doc.chamber == 'S') & (
										Source_Doc.name.contains('List of Senate Bills') |
										Source_Doc.name == 'S bills'
									)
							):

			print ' Getting bill links for {0} {1}...'.format(
							  bills_list_page.chamber.id
							, session.name
					)

			directory = bills_list_page.file_name.split('/')
			del directory[-1]
			directory.append('bills')

			directory = '/'.join(directory)
			
			if not os.path.exists(directory):
				os.makedirs(directory)

			# get the content of the bill list page (includes downloading, if necessary)
			content = None

			while content == None:
				try:
					content = get_content(bills_list_page, requests_session)
				except requests.exceptions.ConnectionError as e:
					print e
					print '   Connection failed. Retrying...'
					requests_session = requests.session()
				except Exception as e:
					print e

			# for each of links extracted from the bill list page...
			for link in extract_links(content, bills_list_page.url):

				# get the name of each link
				name = re.sub('\s{2,}', ' ', link['name']).strip()
				# if the name matches the pattern of a bill name...
				if re.match('\D+\s\d+', name):

					# set these link values
					link['session'] = session.id
					link['name'] = name
					link['parent'] = bills_list_page.id
					link['file_name'] = '{0}/{1}.html'.format(directory, link['name'].replace(' ', '_'))

					# if necessary, make a source_doc record for the bill details page
					try:
						with db.atomic():
							Source_Doc.create(**link)
					except Exception as e:
						if 'duplicate' in e.message:
							pass
						else:
							print 'Error on line #{0}: {1}'.format(inspect.currentframe().f_lineno, e)

			# for each the bill details pages linked to from the bill list page...
			for bill_details_page in bills_list_page.children:

				print bill_details_page.url

				# set up a bill object to save later
				bill = Bill(
						  session = session.id
						, chamber = bill_details_page.chamber
						, source_doc = bill_details_page
						, stricken_from_calendar = False
					)

				# get the bill's details page contents (download if necessary)
				content = None

				while content == None:
					try:
						content = get_content(bill_details_page, requests_session)
					except requests.exceptions.ConnectionError, e:
						print e
						print '   Connection failed. Retrying...'
						requests_session = requests.session()
					except Exception as e:
						print e

				soup = BeautifulSoup(content, 'html5lib')

				# painful chamber- and year-specific logic starts here
				if bill_details_page.chamber.id == 'H':

					if session.year > 2010:
							
						bill_details = soup.find('div', id = 'BillDetails')

						bill.bill_type = bill_details.find('span', attrs = {'class':'entry-title'}).text.split(' ')[0].strip()
						bill.number = int(bill_details.find('span', attrs = {'class':'entry-title'}).text.split(' ')[1])
						bill.description = bill_details.find('div', attrs = {'class':'BillDescription'}).text.replace('\n',' ').strip('"')

						for tr in bill_details.find('table').findAll('tr'):
							if tr.find('td') != None:
								try:
									header = tr.find('th').text
								except AttributeError:
									pass
								else:
									if header == 'Sponsor:':

										bill.sponsor_string = tr.find('td').text.strip()
											
									if header == 'LR Number:':
										bill.lr_number = tr.find('td').text

									if header in ['Effective Date:', 'Proposed Effective Date:']:
										bill.effective_date = tr.find('td').text

									if header == 'Bill String:':
										bill.bill_string = tr.find('td').text

									if header == 'Co-Sponsor:':
										bill.co_sponsor_string = tr.find('td').text
										bill.co_sponsor_link = tr.find('a')['href'].strip()

						for a_tag in soup.find('div', class_ = 'Sections').find_all('a'):
							if a_tag.text == 'Actions':
								bill.actions_link = a_tag['href']
							elif a_tag.text == 'Co-Sponsors':
								bill.co_sponsor_link = a_tag['href']
				
					elif session.year <= 2010:

						bill_details = soup.find('div', class_ = 'sitebox')

						if bill_details == None:
							bill_details = soup.find('body')

						table_0 = bill_details.find_all('table')[0]

						bill_string = re.search('(\D+)\s*(\d+)', table_0.find('td').find('font').text)

						bill.bill_type = bill_string.group(1).strip()
						# bill.bill_type = table_0.find('td').find('font').text.strip().split()[0]
						bill.number = bill_string.group(2)
						# bill.number = int(table_0.find('td').find('font').text.strip().split()[1])
						bill.description = table_0.find('td').find_next('td').text.replace('\n',' ').strip()

						table_1 = bill_details.find_all('table')[1]

						bill.sponsor_string = table_1.find_all('tr')[0].find_all('td')[1].text.strip()
						
						try:
							bill.effective_date = re.search('\d+\/\d+\/\d+', table_1.find_all('tr')[0].find_all('td')[3].text).group()
						except Exception as e:
							print 'No date found in string: {}'.format(table_1.find_all('tr')[0].find_all('td')[3].text.strip())
							bill.effective_date = table_1.find_all('tr')[0].find_all('td')[3].text.strip()

						co_sponsor_field = table_1.find_all('tr')[1].find_all('td')[1]

						bill.co_sponsor_string = co_sponsor_field.text.replace('\n', '').strip()

						try:
							bill.co_sponsor_link = co_sponsor_field.find('a')['href'].strip()
						except Exception as e:
							bill.co_sponsor_link = None

						bill.lr_number = table_1.find_all('tr')[1].find_all('td')[3].text.strip()					

						bill.actions_link = bill_details.find('center').find('table').find('tr').find('td').find('a')['href'].strip()

				if bill_details_page.chamber.id == 'S':					

					if session.year > 2004:

						bill.bill_string = soup.find('span', id = 'lblBillNum').text.strip()

						bill.bill_type = bill.bill_string.split()[0]

						bill.number = int(bill.bill_string.split()[1])

						bill.description = codecs.encode(soup.find('span', id = 'lblBriefDesc').text.strip(), 'utf-8')

						bill.title = codecs.encode(soup.find('span', id = 'lblBillTitle').text.strip(), 'utf-8')

						bill.lr_number = soup.find('span', id = 'lblLRNum').text.strip()

						bill.sponsor_string = soup.find('a', id = 'hlSponsor').text.strip()

						bill.effective_date = soup.find('span', id = 'lblEffDate').text.strip()

						bill.actions_link = soup.find('a', id = 'hlAllActions')['href']

						try:
							bill.co_sponsor_link = soup.find('a', id = 'hlCoSponsors')['href'].strip()
						except KeyError:
							bill.co_sponsor_link = None
						except Exception as e:
							print type(e)
							print 'Error on line #{0}: {1}'.format(inspect.currentframe().f_lineno, e)

					elif session.year <= 2004:

						if 'Bill Stricken from Calendar' in content:
							bill.stricken_from_calendar = True

						header = soup.find_all('table')[0].find_all('td')

						bill.bill_string = header[0].text.strip()

						bill.bill_type = bill.bill_string.split()[0]

						bill.number = int(bill.bill_string.split()[1])

						bill.description = codecs.encode(header[1].text.strip(), 'utf-8')

						table2_rows = soup.find_all('table')[1].find_all('tr')

						bill.sponsor_string = table2_rows[0].find_all('td')[1].text.strip()

						try:
							bill.co_sponsor_link = table2_rows[0].find_all('td')[2].find('a')['href'].strip()
						except IndexError as e:
							bill.co_sponsor_link = None

						if session.year > 1995:
							bill.lr_number = table2_rows[1].find_all('td')[1].text.strip()
						else:
							bill.lr_number = table2_rows[1].find_all('td')[3].text.strip()

						if session.year > 1995:
							bill.title = table2_rows[4].find_all('td')[1].text.strip()
						else:
							bill.title = table2_rows[3].find_all('td')[1].text.strip()

						if session.year > 1995:
							bill.effective_date = table2_rows[5].find_all('td')[1].text.strip()
						else:
							bill.effective_date = table2_rows[4].find_all('td')[1].text.strip()

						try:
							bill.actions_link = soup.find('a', text = 'All Actions')['href'].strip()
						except TypeError:
							print 'No actions link?'
						except Exception as e:
							print type(e)
							print 'Error on line #{0}: {1}'.format(inspect.currentframe().f_lineno, e)

				for k, v in bill._data.iteritems():
					print '  {0}: {1}'.format(k, v)

				# the action's links are sometimes pointed to an old domain. this should fix those.
				if bill_details_page.chamber.id == 'H':
					if 'www.house.state.mo.us' in bill.actions_link:
						bill.actions_link = 'http://www.house.mo.gov/content.aspx?info={}'.format(urlparse(bill.actions_link).path)

				# try saving the bill to the db, unless it is a duplicate
				try:
					with db.atomic():
						bill.save()
				except Exception as e:
					if 'duplicate' in e.message:
						pass
					else:
						print 'Error on line #{0}: {1}'.format(inspect.currentframe().f_lineno, e)

				# either create or get the source_doc record for the bill's actions page
				try:
					with db.atomic():
						actions_doc = Source_Doc.create(
									  chamber = bill_details_page.chamber
									, scheme = urlparse(bill_details_page.url).scheme
									, netloc = urlparse(bill_details_page.url).netloc
									, path = urlparse(bill.actions_link).path
									, params = urlparse(bill.actions_link).params
									, query = urlparse(bill.actions_link).query
									, fragment = urlparse(bill.actions_link).fragment
									, url = urlunparse((
											  urlparse(bill_details_page.url).scheme
											, urlparse(bill_details_page.url).netloc
											, urlparse(bill.actions_link).path
											, urlparse(bill.actions_link).params
											, urlparse(bill.actions_link).query
											, urlparse(bill.actions_link).fragment
										))
									, name = '{0} actions'.format(bill.bill_string)
									, file_name = '{0}_actions.html'.format(bill_details_page.file_name.rstrip('.html'))
									, parent = bill_details_page.id
									, session = session.id
							)
				except Exception as e:
					if 'duplicate' in e.message:
						actions_doc = Source_Doc.get( 
							  file_name = '{0}_actions.html'.format(bill_details_page.file_name.rstrip('.html'))
							, url = urlunparse((
									  urlparse(bill_details_page.url).scheme
									, urlparse(bill_details_page.url).netloc
									, urlparse(bill.actions_link).path
									, urlparse(bill.actions_link).params
									, urlparse(bill.actions_link).query
									, urlparse(bill.actions_link).fragment
								))
							)
					else:
						print 'Error on line #{0}: {1}'.format(inspect.currentframe().f_lineno, e)

				content = None	

				# read the content of the bill's actions page
				while content == None:
					try:
						content = get_content(actions_doc, requests_session)
					except requests.exceptions.ConnectionError, e:
						print e
						print '   Connection failed. Retrying...'
						sleep(5)
						requests_session = requests.session()
					except Exception as e:
						print 'Error on line #{0}: {1}'.format(inspect.currentframe().f_lineno, e)

				soup = BeautifulSoup(content, 'html5lib')

				actions = []
				
				if bill_details_page.chamber.id == 'H':

					# some of the files point to broken pages. 
					# when those come up, try again to get the content.
					if soup.find('table') == None:
						print '   Broken link. Trying to get the content again...'
						sleep(3)
						response = requests_session.get(actions_doc.url)
						response.raise_for_status()
						content = response.content

						with open(actions_doc.file_name, 'w') as f:
							f.write(content)

						soup = BeautifulSoup(content, 'html5lib')

					# iterate over each table row...
					for tr in soup.find('table').find_all('tr')[1:]:

						tds = tr.find_all('td')

						# skip any row with less than one column
						if len(tds) > 1:

							# if there's actually text in the first column...
							if len(tds[0].text.strip()) > 1:

								bill_action = Bill_Action(
									  bill = bill.id
									, action_date = tds[0].text.strip()
									, description = tds[2].text.strip()
									, source_doc = actions_doc
									, journal_pages = []
								)

								# if there's actually a number in the second column...
								if re.search('\d+', tds[1].text.strip()) != None:

									for page in parse_journal_pages(tds[1]):
										bill_action.journal_pages.append(page)

								# and append the action to the list of actions
								actions.append(bill_action)

							# if there's no date in the first column, just append the text to the previous action description
							else:
								try:
									actions[-1].description += ' | {}'.format(tds[2].text.strip())
								except IndexError:
									# if there's no other action yet, then we just ignore this row
									pass

				elif bill_details_page.chamber.id == 'S':

					if bill.stricken_from_calendar == False:
						
						if session.year > 2004:
							table = soup.find('table', id = 'Table5').find_all('table')[1]
						elif session.year <= 2004:

							try:
								table = soup.find_all('table')[1]
							except:
								# when those come up, try again to get the content.
								print '   Broken link. Trying to get the content again...'
								sleep(3)
								response = requests_session.get(actions_doc.url)
								response.raise_for_status()
								content = response.content

								with open(actions_doc.file_name, 'w') as f:
									f.write(content)

								soup = BeautifulSoup(content, 'html5lib') #was lxml
								table = soup.find_all('table')[1]

						for tr in table.find_all('tr'):

							tds = tr.find_all('td')
							
							# skip any row with less than one column
							if len(tds) > 1:

								# if there's actually text in the first column...
								if len(tds[0].text.strip()) > 1:

									bill_action = Bill_Action(
											  bill = bill.id
											, action_date = tds[0].text.strip()
											, description = tds[1].text.strip()
											, journal_pages = []
											, source_doc = actions_doc
										)

									try:
										bill_action.description_link = tds[1].find('a')['href']
									except (TypeError, IndexError):
										bill_action.description_link = None

									# if there's actually a number in the last column...
									if len(tds) == 3:
										if re.search('\d+', tds[2].text.strip()) != None:

											for page in parse_journal_pages(tds[2]):
												bill_action.journal_pages.append(page)

										# and append the action to the list of actions
										actions.append(bill_action)

								# if there's no date in the first column, just append the text to the previous action description
								else:
									try:
										actions[-1].description += ' | {}'.format(tds[1].text.strip())
									except IndexError:
										# if there's no other action yet, then we just ignore this row
										pass


				order_count = 0
				# now go back over the collected actions
				for action in actions:

					if action.description != '':

						order_count += 1

						action.order = order_count

						# try searching the description field for a 'yes' vote count pattern
						try:
							action.aye_count = re.search('(?:AYES)|(?:YEAS):\s*(\d+)', action.description).group(1)
						except AttributeError:
							pass
						except Exception as e:
							print 'Error on line #{0}: {1}'.format(inspect.currentframe().f_lineno, e)

						# try searching the description field for a 'no' vote count pattern
						try:
							action.no_count = re.search('(?:NOES)|(?:NAYS):\s*(\d+)', action.description).group(1)
						except AttributeError:
							pass
						except Exception as e:
							print 'Error on line #{0}: {1}'.format(inspect.currentframe().f_lineno, e)
						
						# try searching the description field for a 'present' vote count pattern
						try:
							action.present_count = re.search('PRESENT:\s*(\d+)', action.description).group(1)
						except AttributeError:
							pass
						except Exception as e:
							print 'Error on line #{0}: {1}'.format(inspect.currentframe().f_lineno, e)

						for k, v in action._data.iteritems():
							print '    {0}: {1}'.format(k, v)

						# then try saving the bill action
						try:
							with db.atomic():
								action.save()
						except Exception as e:
							if 'duplicate' in e.message:
								pass
							else:
								print 'Error on line #{0}: {1}'.format(inspect.currentframe().f_lineno, e)

						# then save each associated journal page
						for page in action.journal_pages:

							page.bill_action = action.id

							try:
								with db.atomic():
									page.save()
							except Exception as e:
								if 'duplicate' in e.message:
									pass
								else:
									print 'Error on line #{0}: {1}'.format(inspect.currentframe().f_lineno, e)

					print '==========='

end_time = datetime.now()

print 'Finished in {}'.format(str(end_time - start_time))