#!/usr/bin/env python
# -*- coding: utf-8 -*-

from models import *
from urlparse import urlparse

db.create_tables([
				  Source_Page
				, Assembly
				, Chamber
				, Legislator_Assembly
				, Session_Type
				, Session
				, Bill_Type
				, Bill
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