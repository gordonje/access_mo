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


class Committee(BaseModel):
	# Is it the same committees with the same names for all sessions?
	name = CharField()
	chamber = ForeignKeyField(Chamber, related_name = 'committees')
	created_date = DateTimeField(default = datetime.now)


class Person(BaseModel):
	first_name = CharField()
	middle_name = CharField()
	last_name = CharField()
	created_date = DateTimeField(default = datetime.now)

	class Meta:
		indexes = (
			(('first', 'middle', 'last'), True),
		)


class Legislator_Assembly(BaseModel):
	person = ForeignKeyField(Person, related_name = 'terms')
	assembly = ForeignKeyField(Assembly, related_name = 'members')
	chamber = ForeignKeyField(Chamber)
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
	name = CharField()
	created_date = DateTimeField(default = datetime.now)


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
	committee = ForeignKeyField(Committee, null = True)
	effective_date = DateField(null = True)
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


class Bill_Cosponsor(BaseModel):
	bill = ForeignKeyField(Bill, related_name = 'cosponsors')
	created_date = DateTimeField(default = datetime.now)


class Bill_Action(BaseModel):
	bill = ForeignKeyField(Bill, related_name = 'actions')
	action_date = DateField()
	description = CharField()
	journal_page1 = CharField()
	journal_page2 = CharField()
	created_date = DateTimeField(default = datetime.now)


class Bill_Amendment(BaseModel):
	bill = ForeignKeyField(Bill, related_name = 'amendments')
	lr_number = CharField()
	status = CharField()
	StatusDate = CharField()
	created_date = DateTimeField(default = datetime.now)


class Bill_Topic(BaseModel):
	bill = ForeignKeyField(Bill, related_name = 'topics')
	topic = CharField()
	created_date = DateTimeField(default = datetime.now)


class Legislator_Committee(BaseModel):
	# Are the appointments for each session or each assembly?
	legislator_assembly = ForeignKeyField(Legislator_Assembly, related_name = 'committees')
	committee = ForeignKeyField(Committee, related_name = 'legislators')
	# is_chair = BooleanField(default = False)
	created_date = DateTimeField(default = datetime.now)

