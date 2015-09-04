# -*- coding: utf-8 -*-

import codecs
from csv import DictReader, excel
import os
from models import *
import re

for f in os.listdir('csvs/'):
	if 'Bills.txt' in f:
		with codecs.open('csvs/' + f, 'rU', 'UTF-8-SIG') as bill_file:
			print f

			year = re.search('\d{4}', f).group()

			reader = DictReader(bill_file, delimiter='\t')

			for row in reader:

				bill = Bill(
						  session = Session.select().where(
						  		  Session.year_type_num == 1
						  		, Session.session_type == 'R'
						  		, Session.year == re.search('\d{4}', f).group()
						  	).get()
						, bill_string = row['Bill'].strip()
						, title = row['Title'].strip()
						, lr_number = row['LRNum'].strip()
						, description = row['Desc'].strip()
						, combine_with = row['BillCombinedWith'].strip()
						, effective_date = row['EffDate']
						, sponsor_string = row['Sponsor']
						, combined_with = row['BillCombinedWith']
					)

				bill.bill_type = Bill_Type.get(id = bill.bill_string.split()[0])
				bill.number = bill.bill_string.split()[1]

				bill.sponsor = Assembly_Member.select(
												  Assembly_Member, Person
											 ).join(
											 	  Person
											 ).where(
											 	  Person.last_name == bill.sponsor_string
											 	, Assembly_Member.chamber == 'S'
											 	, Assembly_Member.assembly == bill.session.assembly
											 ).get()

				print bill.sponsor.person.last_name

				# bill.save()

# session = ForeignKeyField(Session, related_name = 'bills')
# 	bill_type = ForeignKeyField(Bill_Type)
# 	number = IntegerField()
# 	bill_string = CharField()
# 	title = CharField(null = True)
# 	description = CharField(null = True)
# 	lr_number = CharField()
# 	sponsor = ForeignKeyField(Assembly_Member, null = True, related_name = 'sponsored_bills')
# 	sponsor_string = CharField()
# 	committee = ForeignKeyField(Committee, null = True)
# 	effective_date = CharField()
# 	source_doc = ForeignKeyField(Source_Doc)
# 	created_date = DateTimeField(default = datetime.now)
# 	combined_with = CharField(null = True)


# Title: 
# Bill: SR 750
# Session: R 
# Sponsor: Chappelle-Nadal
# Committee: 
# BillCombinedWith:  
# LRNum: 1505SR.01I
# Desc: Use of Senate Chamber/21st Century Leadership Academy (5-20-15)
# 				try:
# 					Bill.create(**row)


# loop over action files from the csv directory
	# insert bill action records


# loop over co-sponsor files from the csv directory
	# insert co-sponsor records

