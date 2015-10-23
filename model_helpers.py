#!/usr/bin/env python
# -*- coding: utf-8 -*-

from models import *

def get_or_create_person_name(name_dict):
	""" Tries to find an existing person_name record.
		If it can't, creates a new one, along with the associated person record.
		Returns a person_name object.
	"""

	# clean up the name fields
	for k, v in name_dict.iteritems():
		# strip leading and trailing whitespace from all the name fields
		
		# if the field has no value, substitute an empty string (necessary for peewee's matching)
		if v == None:
			name_dict[k] = ''
		# remove '.' and any leading or trailing whitespace from any field name values
		elif k != 'last_name':
			name_dict[k] = v.replace('.', '').strip()
		else:
		# just remove leading and trailing whitespace from last name
			name_dict[k] = v.strip()

	try:
		person_name = Person_Name.get(**name_dict)
	except Person_Name.DoesNotExist:
		with db.atomic():
			person = Person.get_or_create(
				  first_name = name_dict['first_name']
				, middle_name = name_dict['middle_name']
				, last_name = name_dict['last_name']
				, name_suffix = name_dict['name_suffix']
			)

			person_name = Person_Name.create(
				  person = person[0]
				, **name_dict
			)

	return person_name

def get_or_create_person(**kwargs):
	""" Selects an existing Person record.
		First, tries to match on first_name, full middle_name, last_name and name_suffix.
		Then, tries to match on first_name, middle initial, last_name and name_suffix.
		If no such Person exists, creates a new one.
		Returns a Person object.
	"""

	# Remove '.' and spaces from names besides the middle name
	for k, v in kwargs.iteritems():
		if k != 'last_name':
			try:
				kwargs[k] = v.replace('.', '').replace(' ', '')
			except AttributeError:
				pass

	# Try selecting a person with the same first name, middle name, last name and suffix
	try:
		person = Person.select().where(
				  Person.first_name == kwargs['first_name']
				, Person.middle_name == kwargs['middle_name']
				, Person.last_name == kwargs['last_name']
				, Person.name_suffix == kwargs['name_suffix']
			).get()
	except Person.DoesNotExist:
		# Then try to selecting a person with the same first name, middle initial, last name and suffix
		try:
			person = Person.select().where(
				  Person.first_name == kwargs['first_name']
				, fn.Substr(Person.middle_name, 1, 1) == kwargs['middle_name'][0]
				, Person.last_name == kwargs['last_name']
				, Person.name_suffix == kwargs['name_suffix']
			).get()
		except (Person.DoesNotExist, TypeError):
			# If can't match to first name, middle initial, last name and suffix, create a new person
			person = Person.create(
				  first_name = kwargs['first_name']
				, middle_name = kwargs['middle_name']
				, last_name = kwargs['last_name']
				, name_suffix = kwargs['name_suffix']
				, nickname = kwargs['nickname']
			)
		else:
			# If the existing person's middle name is only one character long
			if len(person.middle_name) == 1:
				# Update the middle name
				person.middle_name = kwargs['middle_name']
				person.save()
			# if the existing person's middle name is longer than one character
			elif len(person.middle_name) > 1:
				# and the new person's middle name is also longer than one character
				if len(kwargs['middle_name']) > 1:
					# Then make a new person
					person = Person.create(
						  first_name = kwargs['first_name']
						, middle_name = kwargs['middle_name']
						, last_name = kwargs['last_name']
						, name_suffix = kwargs['name_suffix']
						, nickname = kwargs['nickname']
					)

	return person