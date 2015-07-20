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


class Source_Page(BaseModel):
	url = CharField()
	scheme = CharField()
	netloc = CharField()
	path = CharField()
	params = CharField(null = True)
	query = CharField(null = True)
	fragment = CharField(null = True)
	chamber = CharField()
	year = IntegerField()
	name = CharField()
	file_name = CharField(unique = True)
	parent_id = IntegerField(default = 0)
	created_date = DateTimeField(default = datetime.now)

	class Meta:
		indexes = (
			(('url', 'parent_id'), True),
		)


class Assembly(BaseModel):
	number = IntegerField(primary_key = True)
	name = CharField()
	created_date = DateTimeField(default = datetime.now)


class Chamber(BaseModel):
	id = CharField(primary_key = True)
	name = CharField()
	title = CharField()
	full_title = CharField()
	past_sessions_url = CharField()
	created_date = DateTimeField(default = datetime.now)


class Legislator_Assembly(BaseModel):
	person = ForeignKeyField(Person, related_name = 'terms')
	assembly = ForeignKeyField(Assembly, related_name = 'members')
	chamber = ForeignKeyField()
	party = CharField()
	district = CharField()
	counties = CharField()
	created_date = DateTimeField(default = datetime.now)

	class Meta:
        primary_key = CompositeKey('person', 'assembly')


class Session_Type(BaseModel):
	id = CharField(primary_key = True)
	name = CharField(unique = True)
	created_date = DateTimeField(default = datetime.now)


class Session(BaseModel):
	assembly = ForeignKeyField(Assembly, related_name = 'sessions')
	year = IntegerField()
	session_type = ForeignKeyField(Session_Type)
	name = get_name()
	created_date = DateTimeField(default = datetime.now)

	def get_name(self):
		return '{0} {1}'.format(self.year, self.session_type.name)


class Person(BaseModel):
	first_name = CharField()
	middle_name = CharField()
	last_name = CharField()
	created_date = DateTimeField(default = datetime.now)

	class Meta:
		indexes = (
			(('first', 'middle', 'last'), True),
		)


class Bill_Type(BaseModel):
	id = CharField(primary_key = True)
	description = CharField()
	chamber = ForeignKeyField(Chamber, related_name = 'bill_types')
	created_date = DateTimeField(default = datetime.now)


class Bill(BaseModel):
	session = ForeignKeyField(Session, related_name = 'bills')
	bill_type = ForeignKeyField(Bill_Type)
	number = IntegerField()
	title = CharField(null = True)
	description = CharField()
	lr_number = CharField(null = True)
	sponsor = ForeignKeyField(Legislator_Assembly, related_name = 'sponsored_bills')
	committee = ForeignKeyField(Committee, null = True	)
	effective_date = DateField(null = True)
	EffDate	BillCombinedWith
	created_date = DateTimeField(default = datetime.now)

	class Meta:
		indexes = (
			(('session', 'bill_type', 'number'), True),
		)

	# 	# does the same bill show up in multiple sessions?
	# 	bill_type = ForeignKeyField(Bill_Type)
	# 	number = IntegerField
	# 	brief_desc = TextField()

	# 	sponsor_first_name,
	# 	sponsor_last_name,
	# 	sponsor_district,
	# 	lr_number,
	# 	effective_date,
	# 	last_action_date,
	# 	last_action_desc,
	# 	next_hearing,
	# 	calendar


# class Lawmaker(BaseModel):
# 	first = CharField()
# 	middle = CharField(null = True)
# 	last = CharField()
# 	chamber = CharField()
# 	year = IntegerField()
# 	party = CharField()
# 	district = CharField()
# 	phone = CharField(null = True)
# 	room = CharField(null = True)
# 	fax = CharField(null = True)
# 	email = CharField(null = True)
# 	source_page = ForeignKeyField(Source_Page)
# 	created_date = DateTimeField(default = datetime.now)

# 	class Meta:
# 		indexes = (
# 			(('year', 'district'), True),
		)



	# def full_url():
	# # concatenates url parts, returns a full url
	# 	full_url = '{0}://{1}{2}'.format(self.scheme, self.netloc, self.path)

	# 	if params != None:
	# 		full_url += '/{}'.format(params)

	# 	if query != None:
	# 		full_url += '/{}'.format(query)

	# 	if fragment != None:
	# 		full_url += '/{}'.format(fragment)

	# 	return full_url


# class Role(BaseModel):
# 	name = CharField()
# 	title = CharField()
# 	abbr_title = CharField()
# 	url = CharField()
# 	created_date = DateTimeField(default = datetime.now)




# bill, bill_action, bill_sponsor, bill_topic, bill_type, sponsor_type
# legislator, legislator_term
# session, legislator_term_session
# committee, committee_member
# parties, chambers

# how long are committee appointments? how long are committee chair appointments