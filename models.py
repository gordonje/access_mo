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
	id = IntegerField(primary_key = True, help_text = 'Primary key. Also the general assembly number.')
	name = CharField(help_text = 'E.g., "88th General Assembly"')	
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')
	start_year = IntegerField(help_text = "Four digit year of the first day of the first session of the general assembly. This should be the year after the general election in which members of this assembly were elected.")
	end_year = IntegerField(help_text = "Four digit year of the last day the last session of the general assembly.")


class Session_Type(BaseModel):
	id = CharField(primary_key = True, max_length = 1, help_text = 'Primary key. Either "R" or "E".')
	name = CharField(unique = True, help_text = 'Either "Regular" or "Extraordinary".')
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')


class Session(BaseModel):
	assembly = ForeignKeyField(Assembly, related_name = 'sessions', help_text = 'Foreign key referencing assembly in which session occured.')
	year = IntegerField(help_text = 'Four digit year in which the session occured')
	session_type = ForeignKeyField(Session_Type, help_text = 'Foreign key referencing the type of session (either "Regular" or "Extraordinary").')
	year_type_ord = IntegerField(default = 1, help_text = 'Indicates the order of the session in cases where multiple sessions of the same type occurred in the same year (mostly relevant to Extraordinary sessions).')
	name = CharField(help_text = 'Name of the session as labeled on the House or Senate clerk website.')
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')

	class Meta:
		indexes = (
			(('assembly', 'year', 'session_type', 'year_type_ord'), True),
		)


class Chamber(BaseModel):
	id = CharField(primary_key = True, max_length = 1, help_text = 'Primary key. Either "H" or "S".')
	name = CharField(help_text = 'Either "House" or "Senate".')
	title = CharField(help_text = 'Either "Rep." or "Sen.".')
	full_title = CharField(help_text = 'Either "Representative" or "Senator".')
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')


class Source_Doc(BaseModel):
	name = CharField(help_text = 'Text labeling the link to the source doc.')
	session = ForeignKeyField(Session, null = True, related_name = 'source_docs', help_text = 'Foreign key referencing the session under which the source doc was found.')
	chamber = ForeignKeyField(Chamber, help_text = 'Foreign key referencing the legislative chamber website from which the source doc was collected.')
	url = CharField(help_text = 'Link to the source doc.')
	scheme = CharField(help_text = 'Parsed from the url.')
	netloc = CharField(help_text = 'Parsed from the url.')
	path = CharField(help_text = 'Parsed from the url.')
	params = CharField(null = True, help_text = 'Parsed from the url.')
	query = CharField(null = True, help_text = 'Parsed from the url.')
	fragment = CharField(null = True, help_text = 'Parsed from the url.')
	file_name = CharField(help_text = 'File name and path for local copy of the source doc.')
	parent = ForeignKeyField('self', null = True, related_name = 'children', help_text = 'Foreign key referencing the other source doc that includes the link to this source doc')
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')

	class Meta:
		indexes = (
			(('url', 'parent', 'file_name'), True),
		)


class Person(BaseModel):
	first_name = CharField(help_text = 'Full first name or first initial.')
	middle_name = CharField(null = True, help_text = 'Full middle name or initial.')
	last_name = CharField(help_text = 'Full last name.')
	nickname = CharField(null = True, help_text = 'Alternate name found in (...), as in "Jack (Skip) Johnson".')
	name_suffix = CharField(null = True, help_text = 'E.g., "Sr", "Jr" or "III".')
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')

	class Meta:
		indexes = (
			(('first_name', 'middle_name', 'last_name', 'name_suffix'), True),
		)

class Person_Duplicate(BaseModel):
	person = ForeignKeyField(Person, related_name = 'duplicates', help_text = 'Foreign key referencing most recent record of the distinct person.')
	duplicate = ForeignKeyField(Person, related_name = 'duplicate_of', help_text = 'Foreign key referencing older person record mapped to the most recent distinct person record.')
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')

	class Meta:
		indexes = (
			(('person', 'duplicate'), True),
		)	

# class Legislator(BaseModel):
# 	person = ForeignKeyField(Person, related_name = 'legislative_offices')
# 	chamber = ForeignKeyField(Chamber)
# 	district = IntegerField()
# 	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')

# 	class Meta:
# 		indexes = (
# 			(('person', 'chamber', 'district'), True),
# 		)


class Election_Type(BaseModel):
	id = CharField(primary_key = True, help_text = 'Primary key. Either "G", "S" or "P".')
	name = CharField(unique = True, help_text = 'Either "General", "Special" or "Primary".')
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')


class Election(BaseModel):
	name = CharField(help_text = 'Name of the election as it appears in the SoS election results (e.g., "General Election - November 4, 2014").')
	election_date = DateField(help_text = 'Date that the election was held.')
	election_type = ForeignKeyField(Election_Type, related_name = 'elections', help_text = 'Foreign key referencing the type of election (General, Primary or Special).')
	file_name = CharField(null = True, help_text = 'File path and name of a local copy of the text file of the election results.')
	assembly = ForeignKeyField(Assembly, null = True, related_name = 'elections', help_text = "Foreign key field referencing the assembly to which the legislative race candidates were elected.")
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')


class Race_Type(BaseModel):
	name = CharField(unique = True, help_text = 'Name of the office for which candidates are running in a given race (e.g., "State Senator"). Also includes "Constitutional Amendment" and "Proposition".')
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')


class Race(BaseModel):
	election = ForeignKeyField(Election, related_name = 'races', help_text = 'Foreign key referencing the election when the race was decided.')
	race_type = ForeignKeyField(Race_Type, related_name = 'races', help_text = 'Foreign key referencing the type of race (e.g., "State Senator").')
	district = IntegerField(null = True, help_text = 'Number representing the legislative district for which candidates are running.')
	party = CharField(null = True, help_text = 'For Primary races, the political party whose nomination candidates are running.')
	unexpired = BooleanField(null = True, help_text = 'Not term limited???')
	num_precincts = IntegerField(null = True, help_text = 'Number precincts in which voters are eligible to vote in the race.')
	total_votes = IntegerField(help_text = 'Number of votes cast in the race.')
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')


class Race_Candidate(BaseModel):
	race = ForeignKeyField(Race, related_name = 'candidates', help_text = 'Foreign key referencing the race in which the candidate ran.')
	raw_name = CharField(help_text = 'Full name of the candidate, as it appeared in the SoS election results.')
	person = ForeignKeyField(Person, related_name = 'races', help_text = 'Foreign key referencing the distinct person representing the candidate.')
	party = CharField(help_text = 'Political party of the candidate, as it appeared in the SoS results.')
	votes = IntegerField(help_text = 'Number of votes cast for the given candidate in the given election.')
	pct_votes = FloatField(help_text = 'Votes cast for the given candidate as a percent of total votes cast in the race.')
	race_rank = IntegerField(null = True, help_text = 'Rank among other candidates in the race based on votes received. Winners are ranked 1.')
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')

	class Meta:
		indexes = (
			(('race', 'person'), True), # Was unique on race and raw_name, but see if this works better.
		)


class Assembly_Member(BaseModel):
	assembly = ForeignKeyField(Assembly, related_name = 'members', help_text = 'Foreign key referencing an assembly in which the member served.')
	person = ForeignKeyField(Person, related_name = 'assemblies', help_text = 'Foreign key referencing the distinct person who was the assembly Assembly_Member.')
	chamber = ForeignKeyField(Chamber, help_text = 'Foreign key referencing the chamber in which the member served.')
	party = CharField(null = True, help_text = 'The party which the member caucused with during the assembly.')
	district = IntegerField(help_text = 'Foreign key referencing the district which the assembly member represented.')
	counties = CharField(null = True, help_text = 'The counties which the assembly member represented.')
	race_candidate = ForeignKeyField(Race_Candidate, help_text = "Foreign key referencing the race candidate record in which member was elected to the assembly.")
	source_doc = ForeignKeyField(Source_Doc, null = True)
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')

	class Meta:
		indexes = (
			(('assembly', 'person', 'chamber', 'district'), True),
		)


class District_Vacancy(BaseModel):
	session = ForeignKeyField(Session, related_name = 'vacancies', help_text = 'Foreign key referencing the session in which the district was vacant.')
	chamber = ForeignKeyField(Chamber, related_name = 'vacancies', help_text = 'Foreign key referencing the chamber in which the district was vacant.')
	district = CharField(help_text = 'The district that was vacant in chamber and session.')
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')

	class Meta:
		indexes = (
			(('session', 'chamber', 'district'), True),
		)


class Committee(BaseModel):
	# Is it the same committees with the same names for all sessions?
	chamber = ForeignKeyField(Chamber, related_name = 'committees')
	name = CharField()
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')

	class Meta:
		indexes = (
			(('chamber', 'name'), True),
		)


class Committee_Member(BaseModel):
	# Are the appointments for each session or each assembly?
	committee = ForeignKeyField(Committee, related_name = 'members')
	member = ForeignKeyField(Assembly_Member, related_name = 'committees')
	# is_chair = BooleanField(default = False)
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')

	class Meta:
		indexes = (
			(('committee', 'member'), True),
		)


class Bill_Type(BaseModel):
	id = CharField(primary_key = True, help_text = 'Primary key (e.g., "HB", "SJB").')
	name = CharField(help_text = 'Full name of the bill type (e.g., "House Bill", "Senate Joint Resolution").')
	chamber = ForeignKeyField(Chamber, null = True, related_name = 'bill_types', help_text = "Foreign key referencing the chamber in which bills of this type originate.")
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')


class Bill(BaseModel):
	session = ForeignKeyField(Session, related_name = 'bills', help_text = 'Foreign key referencing the session in which the bill was introduced.')
	bill_type = ForeignKeyField(Bill_Type, help_text = 'Foreign key referencing the type of bill (e.g., "HB", "SJB").')
	number = IntegerField(help_text = 'Bill number describing the order in which it was introduced for the given type and session.')
	bill_string = CharField(null = True, help_text = 'Full name of bill, including type and number.')
	title = CharField(null = True, help_text = 'Title of the bill.')
	description = TextField(null = True, help_text = 'Description of the bill.')
	lr_number = CharField(help_text = 'Legislative research number???')
	sponsor = ForeignKeyField(Assembly_Member, null = True, related_name = 'sponsored_bills', help_text = 'Foreign key referencing the assembly member who introduced the bill.')
	sponsor_string = CharField(null = True, help_text = 'Name of the bill sponsor, as it appears on the House or Senate clerk website.')
	co_sponsor_string = CharField(null = True, help_text = 'Text describing the names of co-sponsors, as it appears on the House or Senate clerk website.')
	co_sponsor_link = CharField(null = True, help_text = 'URL linking to the list of co-sponsors of the bill.')
	committee = ForeignKeyField(Committee, null = True, help_text = 'Foreign key referencing the committee to which the bill was (most recently?) assigned.')
	effective_date = CharField(help_text = 'Date on which the bill would become effective.')
	source_doc = ForeignKeyField(Source_Doc, null = True, help_text = 'Foreign key representing the House or Senate clerk details page.')
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')
	combined_with = CharField(null = True)
	stricken_from_calendar = BooleanField(default = False)

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
	bill = ForeignKeyField(Bill, related_name = 'cosponsors', help_text = 'Foreign key referencing the bill co-sponsored by the member.')
	co_sponsor = ForeignKeyField(Assembly_Member, related_name = 'cosponsored_bills', help_text = 'Foreign key referencing the assembly member that co-sponsored the bill.')
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')

	class Meta:
		indexes = (
			(('bill', 'co_sponsor'), True),
		)


class Bill_Action(BaseModel):
	bill = ForeignKeyField(Bill, related_name = 'actions', help_text = 'Foreign key referencing the bill acted upon.')
	action_date = DateField(help_text = 'Date of legislative action on the bill.')
	description = TextField(help_text = 'Full description of the legislative action.')
	description_link = CharField(null = True, help_text = 'Where avaialbe, URL linking to the journal where the legislative action was described.')
	aye_count = IntegerField(null = True, help_text = 'Where available for voting actions, the number of legislators who voted "aye", as it appears in the bill action description.')
	no_count = IntegerField(null = True, help_text = 'Where available for voting actions, the number of legislators who voted "no", as it appears in the bill action description.')
	present_count = IntegerField(null = True, help_text = 'Where available for voting actions, the number of legislators who voted "present", as it appears in the bill action description.')
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')

	class Meta:
		indexes = (
			(('bill', 'action_date', 'description'), True),
		)

class Bill_Action_Journal_Page(BaseModel):
	bill_action = ForeignKeyField(Bill_Action, related_name = 'journal_pages', help_text = 'Foreign key referencing the bill action.')
	chamber = ForeignKeyField(Chamber, null = True, help_text = 'Foreign key referencing the chamber to which the journal belongs.')
	start_page = IntegerField(help_text = 'Page on which the description of the bill action starts in the legislative journal.')
	end_page = IntegerField(help_text = 'Page on which the description of the bill action ends in the legislative journal.')
	journal_link = CharField(null = True, help_text = 'Where available, URL linking to the journal where the legislative action was described.')
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')


# # Looks like Amendments will be hard to get for historic data.
# # Probably doesn't matter for old bills anyway.
# class Bill_Amendment(BaseModel):
# 	bill = ForeignKeyField(Bill, related_name = 'amendments')
# 	lr_number = CharField()
# 	status = CharField()
# 	status_date = CharField()
#	text = TextField()
#	source_doc = ForeignKeyField(Source_Doc)
# 	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')


# # might also consider collecting the bill fiscal notes
# class Bill_Fiscal_Note(BaseModel):
# 	bill = ForeignKeyField(Bill, related_name = 'fiscal_notes')
# 	description = CharField()
# 	order = IntegerField()
#	text = TextField()
#	source_doc = ForeignKeyField(Source_Doc)
# 	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')


class Bill_Topic(BaseModel):
	bill = ForeignKeyField(Bill, related_name = 'topics')
	topic = CharField()
	created_date = DateTimeField(default = datetime.now, help_text = 'Date and time the record was inserted into the database.')

	class Meta:
		indexes = (
			(('bill', 'topic'), True),
		)

