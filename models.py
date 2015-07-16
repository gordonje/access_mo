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

# class Bill_Type(BaseModel):
# 	short = CharField(primary_key = True)
# 	full = CharField()
# 	chamber = CharField()
# 	created_date = DateTimeField(default = datetime.now)

# 	# does the same bill show up in multiple sessions?
# class Bill(BaseModel):
# 	bill_type = ForeignKeyField(Bill_Type)
# 	number = IntegerField
# 	brief_desc = TextField()
# 	sponsor = ForeignKeyField(Legislator_term_session)

# 	# add methods for showing url_id and display_name
# 	sponsor_first_name,
# 	sponsor_last_name,
# 	sponsor_district,
# 	lr_number,
# 	effective_date,
# 	last_action_date,
# 	last_action_desc,
# 	next_hearing,
# 	calendar

# class Legislator(BaseModel):

# 	state = CharField(primary_key = True)
# 	num_dams = IntegerField()
# 	created_date = DateTimeField(default = datetime.now)

# 	class Meta:
# 		order_by = ('state',)




# bill, bill_action, bill_sponsor, bill_topic, bill_type, sponsor_type
# legislator, legislator_term
# session, legislator_term_session
# committee, committee_member
# parties, chambers

# how long are committee appointments? how long are committee chair appointments