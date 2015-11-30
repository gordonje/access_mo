#!/usr/bin/env python
# -*- coding: utf-8 -*-

from models import *
from model_helpers import parse_name

# query to get all senate bills where the sponsor string is not null
sb_q = (Bill.select()
			.join(Bill_Type)
			.where(
				  (Bill.sponsor_string.is_null(False))
				& (Bill_Type.chamber == 'S')
				)
		)

# loop over all the senate bills...
for bill in sb_q:

	print '   Getting sponsor for {0.bill_type_id} {0.number}'.format(bill)
	print bill.source_doc.url

	# query for member by lower last_name, assembly and chamber
	member_query = (Assembly_Member
						.select()
						.join(Person)
						.where(   
							  (fn.Lower(Person.last_name) == bill.sponsor_string.lower())
							& (Assembly_Member.assembly == bill.session.assembly)
							& (Assembly_Member.chamber == 'S')
							)
						)

	# if there are more than one members...
	if member_query.count() > 1:

		if bill.sponsor_string == 'Scott':
			# HACK
			# we've only found one case of a multiple senators with the same last name in the same assembly
			# but only one of them seems to sponsor any bills

			member_query = (Assembly_Member
								.select()
								.join(Person)
								.where(   
									  (fn.Lower(Person.last_name) == bill.sponsor_string.lower())
									& (Person.first_name == 'Delbert')
									& (Assembly_Member.assembly == bill.session.assembly)
									& (Assembly_Member.chamber == 'S')
									)
								)

	# set up a new bill_sponsor record
	bill_sponsor = Bill_Sponsor(
		  bill = bill
		, sponsor_type = 'S'
		, raw_name = bill.sponsor_string
	)

	try:
		# try getting the member
		bill_sponsor.sponsor = member_query.get()
	except Assembly_Member.DoesNotExist:
		print 'Could not find bill sponsor: {0}'.format(bill.sponsor_string)
	else:
		# if a member is found, try saving the bill_sponsor
		try:
			with db.atomic():
				bill_sponsor.save()
		except IntegrityError as e:
			# sometimes the sponsor appears in the list of co-sponsors
			if 'duplicate' in e.message:
				pass

print 'fin.'