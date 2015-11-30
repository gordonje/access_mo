import requests
from models import *
from model_helpers import get_or_create_source_doc, parse_name
from utils import get_content, extract_links
import os
from time import sleep
import re

# set up the co_sponsors directory in each senate session directory
for session in Session.select():
	file_path = 'past_content/S/' +  session.name.replace(' ', '_') + '/co_sponsors/'

	if not os.path.exists(file_path):
		os.makedirs(file_path)

# query to get all the SBs with a co_sponsor_link
sb_q = (Bill.select(Bill, Session)
			.join(Bill_Type)
			.join(Session, on=Bill.session)
			.where(
				  (Bill_Type.chamber == 'S') 
				& (Bill.co_sponsor_link.is_null(False))
				)
			.order_by(Session.year.desc(), Bill.number)
		)

# set up a requests session 
with requests.session() as requests_session:
	# loop over the SB query results
	for bill in sb_q:
		
		# define the file path
		file_path = 'past_content/S/' +  bill.session.name.replace(' ', '_') + '/co_sponsors/'

		print 'Getting co-sponsors for {0.bill_type.id} {0.number} from {0.session.year}'.format(bill)
		print bill.source_doc.url

		# define the file
		the_file = file_path+str(bill.bill_type.id)+'_'+ str(bill.number)+'_co_sponsors.htm'

		# get or create a source_doc record for the co-sponsor page
		source_doc = get_or_create_source_doc(
				  file_name=the_file
				, name = '{0.bill_type.id} {0.number} co-sponsors'.format(bill)
				, session = bill.session
				, url = bill.co_sponsor_link
				, parent = bill.source_doc
				, chamber = 'S'
			)

		content = None

		# load the content from the co-sponsor page
		while content == None:
			try:
				content = get_content(source_doc, requests_session)
			except requests.exceptions.ConnectionError as e:
				print e
				print '   Connection failed. Retrying...'
				requests_session = requests.session()
			except Exception as e:
				print e

		# loop over the links extracted from the co-sponsor page
		for link in extract_links(content, bill.co_sponsor_link):

			if 'District' in link['name']:

				# parse the name out of the link text
				parse_link_name = parse_name(link['name'])
				if parse_link_name['success']:

					# find the assembly member record
					# first, query with the parsed last name, the district, the chamber and the assembly
					member_query = (Assembly_Member
										.select()
										.join(Person)
										.where(
											  (Person.last_name == parse_link_name['name_dict']['last_name'])
											& (Assembly_Member.district == parse_link_name['name_dict']['district'])
											& (Assembly_Member.chamber == 'S')
											& (Assembly_Member.assembly == bill.session.assembly)
										)
									)
					if member_query.count() == 1:
						a_m = member_query.get()
					elif member_query.count() == 0:
						# second, use the district, chamber and assembly
						member_query = (Assembly_Member
											.select()
											.join(Person)
											.where(
												  (Assembly_Member.district == parse_link_name['name_dict']['district'])
												& (Assembly_Member.chamber == 'S')
												& (Assembly_Member.assembly == bill.session.assembly)
											)
										)
						if member_query.count() == 1:
							a_m = member_query.get()
					else:
						print '   Error: More than one possible match!'
					
					# create a co-sponsor record
					try:
						with db.atomic():
							Bill_Sponsor.create(
									  bill = bill
									, sponsor = a_m
									, raw_name = link['name']
									, sponsor_type = 'C'
								)
					except IntegrityError as e:
						if 'duplicate' in e.message:
							pass
				else:
					print 'Error: Unknown co-sponsor pattern.'
					print repr(link['name'])
		print '---------'

print 'fin.'