#!/usr/bin/env python
# -*- coding: utf-8 -*-

from models import *
from urlparse import urlparse

db.create_tables([
				  Source_Page
				, Assembly
				, Chamber
				, Person
				, Legislator_Assembly
				, Session_Type
				, Session
				, Bill_Type
				, Bill
				, Bill_Cosponsor
				, Bill_Amendment
				, Bill_Action
				, Bill_Topic
				, Committee
				, Legislator_Committee
			], True)


with open('look_ups/session_types.csv', 'rU', ) as f:
	reader = csv.DictReader(f)

	for row in reader:
		try:
			Session_Type.create(**row)
		except IntegrityError:
			print '{} is already inserted.'.format(row['name'])

with open('look_ups/assemblies.csv', 'rU', ) as f:
	reader = csv.DictReader(f)

	for row in reader:
		try:
			Assembly.create(**row)
		except IntegrityError:
			print '{} is already inserted.'.format(row['name'])

with open('look_ups/chambers.csv', 'rU', ) as f:
	reader = csv.DictReader(f)

	for row in reader:
		try:
			Chamber.create(**row)
		except IntegrityError:
			print '{} is already inserted.'.format(row['name'])

with open('look_ups/bill_types.csv', 'rU', ) as f:
	reader = csv.DictReader(f)

	for row in reader:
		try:
			Bill_Type.create(**row)
		except IntegrityError:
			print '{} is already inserted.'.format(row['name'])