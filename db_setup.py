#!/usr/bin/env python
# -*- coding: utf-8 -*-

from models import *
from urlparse import urlparse
import csv

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
			with db.atomic():
				Session_Type.create(**row)
		except Exception, e:
			print e

with open('look_ups/assemblies.csv', 'rU', ) as f:
	reader = csv.DictReader(f)

	for row in reader:
		
		try:
			with db.atomic():
				Assembly.create(**row)
		except Exception, e:
			print e

with open('look_ups/chambers.csv', 'rU', ) as f:
	reader = csv.DictReader(f)

	for row in reader:
		
		try:
			with db.atomic():
				Chamber.create(**row)
		except Exception, e:
			print e

with open('look_ups/bill_types.csv', 'rU', ) as f:
	reader = csv.DictReader(f)

	for row in reader:
		# row['chamber'] = Chamber.get(id = row['chamber'])
		try:
			with db.atomic():
				Bill_Type.create(**row)
		except Exception, e:
			print e

