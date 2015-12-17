#!/usr/bin/env python
# -*- coding: utf-8 -*-

from models import *
import re
from urlparse import urlparse, urlunparse

def normalize_name_fields(name_dict):
	""" Takes a dict of name fields.
		Strips leading and trailing whitespace from each field.
		If the field has no value, substitute an empty string (necessary for peewee's matching).
		Remove '.' from non-last name fields.
		Make sure all name fields are present.
		Return dict of transformed name fields.
	"""
	for k, v in name_dict.iteritems():
		# if the field has no value, substitute an empty string (necessary for peewee's matching)
		if v == None:
			name_dict[k] = ''
		# remove '.' and any leading or trailing whitespace from any field name values
		elif k != 'last_name':
			name_dict[k] = v.replace('.', '').replace('\n', ' ').strip()
		else:
		# just remove leading and trailing whitespace from last name
			name_dict[k] = v.replace('\n', ' ').strip()

	# be sure that middle, suffix and nickname fields exist, even if empty
	if 'middle_name' not in name_dict.iterkeys():
		name_dict['middle_name'] = ''
	if 'name_suffix' not in name_dict.iterkeys():
		name_dict['name_suffix'] = ''
	if 'nickname' not in name_dict.iterkeys():
		name_dict['nickname'] = ''

	return name_dict


def parse_name(name_string):
	""" Takes a string that contains a person's name.
		Tries each name regex pattern until it gets a match.
		If a match is found, normalize the name fields 
		(e.g., remove '.' and leading / trailing whitespace)
		Return a dict of results.
	"""

	patterns = {
		  'first': r'(?P<first_name>[\w\.\']+)'
		, 'mid': r'(?P<middle_name>(?:La\s)?[\w\.]+)'
		, 'initials': r'(\w\.\s\w\.)'
		, 'nick': r'[\(\"\'](?P<nickname>[\w\s\.]+)[\)\"\']'
		, 'last': r'(?P<last_name>(?:St\.\s)?\w+(?:[\'\s-][\w\']+)?(?:[\s\w\']+)?)'
		, 'suf': r'(?P<name_suffix>Jr|Sr|SR|[IV]{1,3})\.?'
		, 'district': r'(?P<district>\d+)'
		, 'etal': r'\.+et\s*al\.'
	}

	formats = [
		  { 'description': 'first last, District ##'
		  , 'regex': re.compile(r'^{first}\s{last},\sDistrict\s{district}$'.format(**patterns))
		  }
		, { 'description': 'first last (##)etal?'
		  , 'regex': re.compile(r'^{first}\s+{last}\s+\({district}\){etal}?$'.format(**patterns))
		  }
		, { 'description': 'last, Dr.? first middle? nickname? (district?)'
		  , 'regex': re.compile(r'^{last},(?:\s+Dr\.)?\s+{first}(?:\s+{mid})?(?:\s+{nick})?\s+\({district}?\)$'.format(**patterns))
		  }
		, { 'description': 'last, first mi (district)etal?'
		  , 'regex': re.compile(r'^{last},\s+{first}\s+(?P<middle_name>{initials})\s+\({district}\)?{etal}?$'.format(**patterns))
		  }
		, { 'description': 'first middle last suffix'
		  , 'regex': re.compile(r'^{first}\s{mid}\s{last}?\s{suf}$'.format(**patterns))
		  }
		, { 'description': 'first last,? suffix'
		  , 'regex': re.compile(r'^{first}\s{last},?\s{suf}$'.format(**patterns)) 
		  }
		, { 'description': 'Dr.? first middle? nickname? last,? suffix?'
		  , 'regex': re.compile(r'^(?:Dr\.\s)?{first}(?:\s{mid})?(?:\s{nick})?\s{last}(?:,?\s{suf})?(?:,?\sM\.?D\.?)?$'.format(**patterns)) 
		  }
		, { 'description': 'first mi? last'
		  , 'regex': re.compile(r'^{first}(?:\s(?P<middle_name>{initials}))?\s{last}$'.format(**patterns)) 
		  }
		, { 'description': 'last,? suffix?, first middle? nickname?'
		  , 'regex': re.compile(r'^{last}(?:,?\s{suf})?,\s{first}(?:\s{mid})?(?:\s{nick})?$'.format(**patterns))
		  }
		, { 'description': 'last,? suffix?, first nickname? middle?'
		  , 'regex': re.compile(r'^{last}(?:,?\s{suf})?,\s{first}(?:\s{nick})?(?:\s{mid})?$'.format(**patterns))
		  }
		, { 'description': 'last ?, first nickname? middle? suffix?'
		  , 'regex': re.compile(r'^{last}\s?,\s{first}(?:\s{nick})?(?:\s{mid})?(?:\s{suf})?$'.format(**patterns))
		  }
		, { 'description': 'last, fi nickname? middle? suffix?'
		  , 'regex': re.compile(r'^{last},\s(?P<first_name>{initials})(?:\s{nick})?(?:\s{mid})?(?:\s{suf})?$'.format(**patterns))
		  }
		, { 'description': 'last, first middle ?nickname'
		  , 'regex': re.compile(r'^{last},\s{first}\s{mid}\s?{nick}$'.format(**patterns))
		  }
		, { 'description': 'last, first mi'
		  , 'regex': re.compile(r'^{last},\s{first}\s(?P<middle_name>{initials})$'.format(**patterns))
		  }
		, { 'description': 'last, first mi middle'
		  , 'regex': re.compile(r'^{last},\s{first}\s(?P<middle_name>\w\.\s\w+)$'.format(**patterns))
		  } 
		, { 'description': 'last, nickname first'
		  , 'regex': re.compile(r'^{last},\s{nick}\s{first}?$'.format(**patterns))
		  }
		, { 'description': 'last, nickname first middle'
		  , 'regex': re.compile(r'^{last},\s{nick}\s{first}\s{mid}$'.format(**patterns))
		  }
		, { 'description': 'last, first middle'
		  , 'regex': re.compile(r'^{last},\s{first}\s(?P<middle_name>\w+\s\w+)$'.format(**patterns))
		  }
	]

	results = {'success': False}
	
	for i in formats:

		name_match = re.match(i['regex'], name_string)
		
		if name_match != None: 
			results['success'] = True
			results['match_pattern'] = i['description']
			results['name_dict'] = normalize_name_fields(name_match.groupdict())
			break

	if results['success'] == False:
		print 'Could not parse string: {}'.format(name_string)

	return results


def match_person(first_name = '', middle_name = '', last_name = '', name_suffix = '', nickname = ''):
	""" Takes a dict of name fields.
		Tries multiple different Person select queries.
		Returns the Person object of the first query that has exactly one result.
	"""

	# will hold all select queries to try for this person
	qs_to_run = []

	all_last_names = re.findall(r'([A-Z\'][a-z\']+)', last_name)
	# check if provided multiple last names
	if len(all_last_names) > 1:

		like_last = '%'.join(all_last_names)

		# exact match for first and suffix and stored last matches provided last stripped of non-word characters
		qs_to_run.append(
			Person.select(
				 ).where(
					  (Person.first_name == first_name)
					& (Person.last_name % like_last)
					& (Person.name_suffix == name_suffix)
				 )
			)

		# exact match for first and suffix and concat of stored middle/last matches provided last stripped of non-word characters
		qs_to_run.append(
			Person.select(
				 ).where(
					  (Person.first_name == first_name)
					& (Person.middle_name.concat(Person.last_name) % like_last)
					& (Person.name_suffix == name_suffix)
				 )
			)
	
	# check to see if amiddle name value was provided
	if len(middle_name) > 0:

		# check to see if only a middle initial was provided
		if len(middle_name) == 1:

			# exact match for first, last and suffix, first char of stored middle matches provided middle
			qs_to_run.append(
				Person.select(
					 ).where(
					 	  (Person.first_name == first_name)
					 	& (Person.middle_name.startswith(middle_name))
					 	& (Person.last_name == last_name)
						& (Person.name_suffix == name_suffix)
			 		 )
				)
		else:
			# exact match for first, last and suffix and first char of provided middle matches stored middle
			qs_to_run.append(
				Person.select(
					 ).where(
						  (Person.first_name == first_name)
						& (Person.middle_name == middle_name)
						& (Person.last_name == last_name)
						& (Person.name_suffix == name_suffix)
					 )
				)

		like_first_middle = '{0}%{1}'.format(first_name, middle_name)
		# exact match for last and suffix, stored first matches concat of provided first/middle
		qs_to_run.append(
			Person.select(
				 ).where(
					  (Person.first_name % like_first_middle)
					& (Person.last_name == last_name)
					& (Person.name_suffix == name_suffix)
				 )
			)

		like_middle_last = '{0}%{1}'.format(middle_name, last_name)
		# exact match for first and suffix, stored last matches concat of provided middle/last
		qs_to_run.append(
			Person.select(
				 ).where(
					  (Person.first_name == first_name)
					& (Person.last_name % like_middle_last)
					& (Person.name_suffix == name_suffix)
				 )
			)

		# exact match for last and suffix, stored first matches provided middle
		qs_to_run.append(
			Person.select(
				 ).where(
					  (Person.first_name == middle_name)
					& (Person.last_name == last_name)
					& (Person.name_suffix == name_suffix)
				 )
			)

	else:
		# if no middle name was provided...
		# exact match on first, last and suffix
		qs_to_run.append(
			Person.select(
				 ).where(
					  (Person.first_name == first_name)
					& (Person.last_name == last_name)
					& (Person.name_suffix == name_suffix)
				 )
			)

	# check to see if a nickname was provided
	if len(nickname) > 0:
		
		# exact match on last and suffix, provided nickname matches stored first name
		qs_to_run.append(
			Person.select(
				 ).where(
					  (Person.first_name == nickname)
					& (Person.last_name == last_name)
					& (Person.name_suffix == name_suffix)
				 )
			)

	# check to see if the provided first name is a formal name with diminutives
	try:
		formal_name = Formal_Name.get(Formal_Name.name == first_name)
	except Formal_Name.DoesNotExist:
		# if provided first name is not formal, it could be a diminutive of a stored first name
		# exact match of last and suffix, diminutive of stored first name matches provided first name
		qs_to_run.append(
			Person.select(
				 ).join(Formal_Name, on=(Person.first_name == Formal_Name.name)
				 ).join(Diminutive_Name
				 ).where(
				 	  (Diminutive_Name.name == first_name)
				 	& (Person.last_name == last_name)
					& (Person.name_suffix == name_suffix)
		 		 )
			)
	else:
		# if the provided first name is a formal name with diminutives...
		dimins = []
		for i in formal_name.diminutives:
			dimins.append(i.name)
		# exact match of last and suffix, diminutive of provided first name matches stored first name
		qs_to_run.append(
			Person.select(
				 ).where(
				 	  (Person.first_name << dimins)
				 	& (Person.last_name == last_name)
					& (Person.name_suffix == name_suffix)
		 		 )
			)

	# the following queries will always be attempted (if none of the above succeed)
	# exact match on last and suffix, stored nickname matches provided first name
	qs_to_run.append(
		Person.select(
			 ).where(
			 	  (Person.nickname == first_name)
			 	& (Person.last_name == last_name)
				& (Person.name_suffix == name_suffix)
	 		 )
		)

	like_first = re.sub(r'\W', '%', first_name)
	# exact match on last and suffix, concat of stored first and middle matches provided first
	qs_to_run.append(
		Person.select(
			 ).where(
				  (Person.first_name.concat(Person.middle_name) % like_first)
				& (Person.last_name == last_name)
				& (Person.name_suffix == name_suffix)
			 )
		)

	# exact match on first and suffix, concat of stored middle and last matches provided last
	qs_to_run.append(
		Person.select(
			 ).where(
				  (Person.first_name.concat(Person.middle_name) % like_first)
				& (Person.last_name == last_name)
				& (Person.name_suffix == name_suffix)
			 )
		)

	# exact match on last and suffix, stored middle matches provided first
	qs_to_run.append(
			Person.select(
				 ).where(
					  (Person.middle_name == first_name)
					& (Person.last_name == last_name)
					& (Person.name_suffix == name_suffix)
				 )
			)	

	results = {'found': False}

	# now loop over the queries
	for q in qs_to_run:
		if q.count() == 1:
			results['person'] = q.get()
			results['found'] = True
			break

	return results


def get_or_create_person(name_dict):
	""" Takes a dict of name fields.
		Looks up the Person_Name (combo of first_name, middle_name, last_name, name_suffix, nickname).
		If fails, looks up the Person (combo of first_name, middle_name, last_name, name_suffix).
		If fails, tries to match the name to an existing Person (calls match_person).
		If fails, creates a new Person with an new associated Person_Name.
		Returns the Person record.
	"""
	results = {
		  'new_person': False
		, 'new_person_name': False
		, 'person': None
	}

	# first, try getting a stored Person Name
	try:
		results['person'] = Person_Name.get(**name_dict).person
	except Person_Name.DoesNotExist:
		# second, try getting a stored Person
		try:
			results['person'] = Person.get(
					  Person.first_name == name_dict['first_name']
					, Person.middle_name == name_dict['middle_name']
					, Person.last_name == name_dict['last_name']
					, Person.name_suffix == name_dict['name_suffix']
				)
		except Person.DoesNotExist:
			# if exact person record can't be found, try fuzzy match
			match_attempt = match_person(**name_dict)

			if match_attempt['found'] == False:
				
				results['new_person'] = True
				# if it doesn't succeed, make a new person record
				print '    New person: {first_name} {middle_name} {last_name} {name_suffix}'.format(**name_dict)
				with db.atomic():
					results['person'] = Person.create(**name_dict)
			else:
				results['person'] = match_attempt['person']

		results['new_person_name'] = True
		# create a Person_Name record for the new or found person
		with db.atomic():
			new_name = Person_Name.create(
					  person = results['person']
					, **name_dict
				)
	
	if results['new_person_name']:

		if len(results['person'].middle_name) <= 1:
			if len(new_name.middle_name) > 1:
				results['person'].middle_name = new_name.middle_name
				results['person'].save()

		if results['person'].nickname == '':
			if new_name.nickname != '':
				results['person'].nickname = new_name.nickname
				results['person'].save()
		# might need to figure out how to preserve the formal name in Person.first_name
		# and the "full" last name in Person.last_name

	return results
				

def get_or_create_source_doc(**kwargs):
	""" Takes keyword arguments.
		Tries to select an existing source_doc.
		If there isn't one, creates a new source doc.
		Returns a source doc object.
	"""

	source_doc = None

	try:
		source_doc = Source_Doc.select().where(
					  Source_Doc.file_name == kwargs['file_name']
					, Source_Doc.url == kwargs['url']
					, Source_Doc.parent == kwargs['parent']
			   ).get()
	except Source_Doc.DoesNotExist:
		with db.atomic():
			source_doc = Source_Doc.create(
						  chamber = kwargs['chamber']
						, scheme = urlparse(kwargs['url']).scheme
						, netloc = urlparse(kwargs['url']).netloc
						, path = urlparse(kwargs['url']).path
						, params = urlparse(kwargs['url']).params
						, query = urlparse(kwargs['url']).query
						, fragment = urlparse(kwargs['url']).fragment
						, url = kwargs['url']
						, name = kwargs['name']
						, file_name = kwargs['file_name']
						, parent = kwargs['parent']
						, session = kwargs['session']
			)
	except Exception as e:
		print 'Could not create or get source doc.'
		print e
	
	return source_doc


def get_party(party_string):
	""" Takes a string.
		Depending on the length of the string, selects the party by id, short_name or name.
		Returns a party or none, if no party.
	"""

	if len(party_string) == 1:
		q = Party.select().where(fn.Lower(Party.id) == party_string.lower())
	elif len(party_string) <= 3:
		q = Party.select().where(fn.Lower(Party.short_name) == party_string.lower())
	else:
		q = Party.select().where(fn.Lower(Party.name) == party_string.lower())

	try:
		party = q.get()
	except Party.DoesNotExist:
		if party_string == 'Democrat':
			party = Party.get(id='D')
		elif re.match(r'^WI\d+$', party_string) != None:
			party = Party.get(id='W')
		else:
			print 'Party not known: {}'.format(party_string)
			party = None

	return party


# def get_assembly_member(first_initial, last_name, assembly, chamber, district):
# 	""" Takes a name dict.
# 		Selects all person_name records that match the name dict.
# 		If it fails, tries to match to a person.
# 		Selects a member for the given person, assembly and district.
# 		Returns an assembly_member object.
# 	"""

# 	member = None

# 	like_first = re.sub(r'\W', '%', name_dict['first_name'])
# 	like_last = re.sub(r'\W', '%', name_dict['last_name'])

# 	person_name_q = (Person_Name
# 				.select(Person_Name.person)
# 				.where(
# 					  (Person_Name.first_name % like_first)
# 					& (Person_Name.last_name % like_last)
# 				)
# 		)

# 	if person_name_q.count() == 0:
# 		person_name_q = (Person_Name
# 			.select(Person_Name.person)
# 			.where(
# 				  (Person_Name.last_name == name_dict['last_name'])
# 				& (Person_Name.first_name.startswith(name_dict['first_name'][0]))
# 			)
# 		)

# 	try:
# 		member = Assembly_Member.select().where(
# 				  (Assembly_Member.person << person_name_q)
# 				& (Assembly_Member.assembly == assembly)
# 				& (Assembly_Member.chamber == chamber)
# 				& (Assembly_Member.district == district)
# 			)
# 	except Assembly_Member.DoesNotExist:
# 		person = match_person(**name_dict)['person']

# 		member = Assembly_Member.select().where(
# 				  (Assembly_Member.person == person)
# 				& (Assembly_Member.assembly == assembly)
# 				& (Assembly_Member.chamber == chamber)
# 				& (Assembly_Member.district == district)
# 			)

# 	return member


