#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from sys import argv
from getpass import getpass
from peewee import *

########## Set up database connection ##########

try:
	db_name = argv[1]
except IndexError:
	db_name = raw_input('Enter db name:')
try:
	db_user = argv[2]
except IndexError:
	db_user = raw_input('Enter db user name:')
try:
	db_password = argv[3]
except IndexError:
	db_password = getpass('Enter db user password:')

db = PostgresqlDatabase(db_name, user=db_user, password=db_password)
db.connect()

################################################

class BaseModel(Model):
	class Meta:
		database = db


class Assembly(BaseModel):
	id = IntegerField(primary_key = True)
	name = CharField()	
	created_date = DateTimeField(default = datetime.now)
	start_year = IntegerField()
	end_year = IntegerField()


class Session_Type(BaseModel):
	id = CharField(primary_key = True)
	name = CharField(unique = True)
	created_date = DateTimeField(default = datetime.now)


class Session(BaseModel):
	assembly = ForeignKeyField(Assembly, related_name = 'sessions')
	year = IntegerField()
	session_type = ForeignKeyField(Session_Type)
	year_type_num = IntegerField(default = 1)
	name = CharField()
	created_date = DateTimeField(default = datetime.now)

	class Meta:
		indexes = (
			(('assembly', 'year', 'session_type', 'year_type_num'), True),
		)


class Chamber(BaseModel):
	id = CharField(primary_key = True)
	name = CharField()
	title = CharField()
	full_title = CharField()
	created_date = DateTimeField(default = datetime.now)


class Source_Doc(BaseModel):
	name = CharField()
	session = ForeignKeyField(Session, null = True, related_name = 'source_docs')
	chamber = ForeignKeyField(Chamber)
	url = CharField()
	scheme = CharField()
	netloc = CharField()
	path = CharField()
	params = CharField(null = True)
	query = CharField(null = True)
	fragment = CharField(null = True)
	file_name = CharField()
	parent = ForeignKeyField('self', null = True, related_name = 'children')
	created_date = DateTimeField(default = datetime.now)

	class Meta:
		indexes = (
			(('url', 'parent', 'file_name'), True),
		)


class Person(BaseModel):
	first_name = CharField()
	middle_name = CharField(null = True)
	last_name = CharField()
	created_date = DateTimeField(default = datetime.now)

	class Meta:
		indexes = (
			(('first_name', 'last_name'), True),
		)


class Assembly_Member(BaseModel):
	assembly = ForeignKeyField(Assembly, related_name = 'members')
	person = ForeignKeyField(Person, related_name = 'terms')
	chamber = ForeignKeyField(Chamber)
	party = CharField(null = True)
	district = CharField()
	counties = CharField(null = True)
	source_doc = ForeignKeyField(Source_Doc)
	created_date = DateTimeField(default = datetime.now)

	class Meta:
		indexes = (
			(('assembly', 'person', 'chamber'), True),
		)


class District_Vacancy(BaseModel):
	session = ForeignKeyField(Session, related_name = 'vacancies')
	chamber = ForeignKeyField(Chamber, related_name = 'vacancies')
	district = CharField()
	created_date = DateTimeField(default = datetime.now)

	class Meta:
		indexes = (
			(('session', 'chamber', 'district'), True),
		)


class Committee(BaseModel):
	# Is it the same committees with the same names for all sessions?
	chamber = ForeignKeyField(Chamber, related_name = 'committees')
	name = CharField()
	created_date = DateTimeField(default = datetime.now)

	class Meta:
		indexes = (
			(('chamber', 'name'), True),
		)

class Committee_Member(BaseModel):
	# Are the appointments for each session or each assembly?
	committee = ForeignKeyField(Committee, related_name = 'members')
	member = ForeignKeyField(Assembly_Member, related_name = 'committees')
	# is_chair = BooleanField(default = False)
	created_date = DateTimeField(default = datetime.now)

	class Meta:
		indexes = (
			(('committee', 'member'), True),
		)


class Bill_Type(BaseModel):
	id = CharField(primary_key = True)
	name = CharField()
	chamber = ForeignKeyField(Chamber, null = True, related_name = 'bill_types')
	created_date = DateTimeField(default = datetime.now)


class Bill(BaseModel):
	session = ForeignKeyField(Session, related_name = 'bills')
	bill_type = ForeignKeyField(Bill_Type)
	number = IntegerField()
	bill_string = CharField()
	title = CharField(null = True)
	description = CharField(null = True)
	lr_number = CharField()
	sponsor = ForeignKeyField(Assembly_Member, null = True, related_name = 'sponsored_bills')
	sponsor_string = CharField()
	committee = ForeignKeyField(Committee, null = True)
	effective_date = CharField()
	source_doc = ForeignKeyField(Source_Doc)
	created_date = DateTimeField(default = datetime.now)
	# BillCombinedWith
	# last_action_date,
	# last_action_desc,
	# next_hearing,
	# calendar

	# can the same bill show up in a regular and extraordinary session?
	
	class Meta:
		indexes = (
			(('session', 'bill_type', 'number'), True),
		)


class Bill_Summary(BaseModel):
	bill = ForeignKeyField(Bill, related_name = 'summary_versions')
	description = CharField()
	order = IntegerField()
	summary = TextField()
	source_doc = ForeignKeyField(Source_Doc)	


class Bill_Text(BaseModel):
	bill = ForeignKeyField(Bill, related_name = 'text_versions')
	description = CharField()
	order = IntegerField()
	text = TextField()
	source_doc = ForeignKeyField(Source_Doc)


class Bill_Cosponsor(BaseModel):
	bill = ForeignKeyField(Bill, related_name = 'cosponsors')
	co_sponsor = ForeignKeyField(Assembly_Member, related_name = 'cosponsored_bills')
	created_date = DateTimeField(default = datetime.now)

	class Meta:
		indexes = (
			(('bill', 'co_sponsor'), True),
		)


class Bill_Action(BaseModel):
	bill = ForeignKeyField(Bill, related_name = 'actions')
	action_date = DateField()
	description = CharField()
	journal_page1 = CharField()
	journal_page2 = CharField()
	created_date = DateTimeField(default = datetime.now)


# # Looks like Amendments will be hard to get for historic data.
# # Probably doesn't matter for old bills anyway.
# class Bill_Amendment(BaseModel):
# 	bill = ForeignKeyField(Bill, related_name = 'amendments')
# 	lr_number = CharField()
# 	status = CharField()
# 	status_date = CharField()
#	text = TextField()
#	source_doc = ForeignKeyField(Source_Doc)
# 	created_date = DateTimeField(default = datetime.now)


# # might also consider collecting the bill fiscal notes
# class Bill_Fiscal_Note(BaseModel):
# 	bill = ForeignKeyField(Bill, related_name = 'fiscal_notes')
# 	description = CharField()
# 	order = IntegerField()
#	text = TextField()
#	source_doc = ForeignKeyField(Source_Doc)
# 	created_date = DateTimeField(default = datetime.now)


class Bill_Topic(BaseModel):
	bill = ForeignKeyField(Bill, related_name = 'topics')
	topic = CharField()
	created_date = DateTimeField(default = datetime.now)

	class Meta:
		indexes = (
			(('bill', 'topic'), True),
		)

