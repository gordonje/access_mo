#!/usr/bin/env python
# -*- coding: utf-8 -*-

from models import *
from model_helpers import parse_name, get_or_create_person
import re
import requests
from bs4 import BeautifulSoup
from time import sleep

def get_hb_sponsor(bill, sponsor_type):
	""" Takes a bill and a sponsor type. 
		Parse out the name, and queries to find the member's record.
		Returns a Bill_Sponsor object, ready to save.
	"""

	bill_sponsor = Bill_Sponsor(
		  bill = bill
		, sponsor_type = sponsor_type
	)

	if sponsor_type == 'S':
		bill_sponsor.raw_name = bill.sponsor_string
	elif sponsor_type == 'C':
		bill_sponsor.raw_name = bill.co_sponsor_string

	# parse the district from the raw_name
	try:
		district = re.search(r'\((\d+)\)', bill_sponsor.raw_name).group(1)
	except AttributeError:
		# if this fails, set up the first query to fail and deal with it downstream
		district = 0
	
	# query for member by district, assembly and chamber
	member_query = (Assembly_Member
						.select()
						.where(   
							  (Assembly_Member.district == district)
							& (Assembly_Member.assembly == bill.session.assembly)
							& (Assembly_Member.chamber == 'H')
							)
						)

	# if there's only one result in the member query, use that member
	if member_query.count() == 1:
		bill_sponsor.sponsor = member_query.get()
	# if there are more than one members...
	elif member_query.count() != 1:
		# for some reason, these two legislator names are sometimes formatted differently
		if 'Stacey Newman' in bill_sponsor.raw_name:
			last = 'Newman'
		elif 'Scharnhorst' in bill_sponsor.raw_name:
			last = 'Scharnhorst'
		else:
			last = re.search(r'^([\w-]+)(?:\s\w+)?,', bill_sponsor.raw_name).group(1)
		
		if district > 0:
			# query for member by last_name, district, assembly and chamber
			member_query = (Assembly_Member
						.select()
						.join(Person)
						.where(   
							  (Person.last_name == last)
							& (Assembly_Member.district == district)
							& (Assembly_Member.assembly == bill.session.assembly)
							& (Assembly_Member.chamber == 'H')
							)
						)
		elif district == 0:
			# query for member by last_name, assembly and chamber
			member_query = (Assembly_Member
						.select()
						.join(Person)
						.where(   
							  (Person.last_name == last)
							& (Assembly_Member.assembly == bill.session.assembly)
							& (Assembly_Member.chamber == 'H')
							)
						)

		if member_query.count() == 1:
			bill_sponsor.sponsor = member_query.get()
		else:
			# remove the 'etal' from the raw_name
			name_string = re.sub(r'[\.\s]+et\s*al\.*', '', bill_sponsor.raw_name).strip()
			
			# parse the name
			parsed_name = parse_name(name_string)
			
			# remove the district
			district = parsed_name['name_dict'].pop('district')
			
			# get or create a person
			person = get_or_create_person(parsed_name['name_dict'])['person']
			
			# get or create an assembly_member
			with db.atomic():
				bill_sponsor.sponsor = Assembly_Member.get_or_create(
						  person = person
						, district = district
						, assembly = bill.session.assembly
						, chamber = 'H'
					)[0]

	# save the new bill_sponsor record
	return bill_sponsor


# query to get all house bills where the sponsor string is not null
hb_q = (Bill.select()
			.join(Bill_Type)
			.where(
				  (Bill_Type.chamber == 'H')
				& (Bill.bill_type != 'HEC')
				& (
					(
					  (Bill.sponsor_string.is_null(False))
					& (fn.Char_Length(Bill.sponsor_string) > 2)
					)
				  | (
					  (Bill.co_sponsor_string.is_null(False))
					& (fn.Char_Length(Bill.co_sponsor_string) > 2)
					& ~(Bill.co_sponsor_string.regexp(r'^[.\s]+etal\.*$'))
					)
				)
			)
		)

# # loop over all the house bills...
# for bill in hb_q:

# 	print '   Working on {0.bill_type_id} {0.number}'.format(bill)
# 	print bill.source_doc.url

# 	if bill.sponsor_string == None or len(bill.sponsor_string) <= 2:
# 		print '      No sponsor.'
# 	else:
# 		print '      Getting sponsor...'
# 		hb_spon = get_hb_sponsor(bill, 'S')
# 		with db.atomic():
# 			hb_spon.save()

# 	if bill.co_sponsor_string == None or len(bill.co_sponsor_string) <= 2 or re.match(r'^[.\s]+etal\.*$', bill.co_sponsor_string) != None:
# 		print '      No co-sponsor.'
# 	else:
# 		print '      Getting co-sponsor...'
# 		hb_co_spon = get_hb_sponsor(bill, 'C')
		
# 		try:
# 			with db.atomic():
# 				hb_co_spon.save()
# 		except IntegrityError as e:
# 			# sometimes the sponsor appears in the list of co-sponsors
# 			if 'duplicate' in e.message:
# 				pass

# 	print '--------------'

# some of the more recent house bills have a link to a page that lists all the co-sponsors
hb_w_co_spon_link_q = (Bill.select()
			.join(Bill_Type)
			.where(
				  (Bill_Type.chamber == 'H')
				& (Bill.bill_type != 'HEC')
				& (Bill.co_sponsor_link.contains('CoSponsors.aspx'))
			)
	)

# set up a requests session for pages we don't have yet:
with requests.session() as requests_session:
	for bill in hb_w_co_spon_link_q:

		print 'http://www.house.mo.gov/' + bill.co_sponsor_link

		r = None

		while r == None:
			try:
				r = requests_session.get('http://www.house.mo.gov/' + bill.co_sponsor_link)
			except requests.exceptions.ConnectionError as e:
				print e
				print '   Connection failed. Retrying...'
				requests_session = requests.session()
			except Exception as e:
				print e

		soup = BeautifulSoup(r.content, 'html5lib')

		table = soup.find(id = 'ContentPlaceHolder1_grdCoSponsors_DXMainTable')

		for tr in soup.find_all('tr', class_ = 'dxgvDataRow'):

			tds = tr.find_all('td')

			bill_co_sponsor = Bill_Sponsor(
				  bill = bill
				, sponsor_type = 'C'
				, raw_name = tds[0].text.strip()
			)

			district = tds[1].text.strip()

			# query for member by district, assembly and chamber
			member_query = (Assembly_Member
								.select()
								.where(   
									  (Assembly_Member.district == district)
									& (Assembly_Member.assembly == bill.session.assembly)
									& (Assembly_Member.chamber == 'H')
									)
								)

			# if there's only one result in the member query, use that member
			if member_query.count() == 1:
				bill_co_sponsor.sponsor = member_query.get()
			# if there are more than one members...
			elif member_query.count() != 1:

				parsed_name = parse_name(bill_co_sponsor.raw_name)['name_dict']

				# query for member by last_name, district, assembly and chamber
				member_query = (Assembly_Member
							.select()
							.join(Person)
							.where(   
								  (Person.last_name == parsed_name['last_name'])
								& (Assembly_Member.district == district)
								& (Assembly_Member.assembly == bill.session.assembly)
								& (Assembly_Member.chamber == 'H')
								)
							)

				if member_query.count() == 1:
					bill_co_sponsor.sponsor = member_query.get()
				else:
					print 'Error: Could not find co-sponsor!'
					print bill_co_sponsor.raw_name

			print bill_co_sponsor.sponsor.person.last_name

			try:
				with db.atomic():
					bill_co_sponsor.save()
			except IntegrityError as e:
				# sometimes the sponsor appears in the list of co-sponsors
				if 'duplicate' in e.message:
					pass


		sleep(3)
		print '=========='






print 'fin.'