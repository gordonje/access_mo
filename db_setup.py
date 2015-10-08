#!/usr/bin/env python
# -*- coding: utf-8 -*-

from models import *
from urlparse import urlparse
from csv import DictReader

tables = []

# read in table_names from tables.tsv
with open('record_layouts/tables.tsv', 'rU', ) as f:
	reader = DictReader(f, delimiter='\t')

	for row in reader:
		tables.append(globals()[row['table'].title()])

db.create_tables(tables, True)

# inserting all the look-up records.

with open('look_ups/assemblies.csv', 'rU', ) as f:
	reader = DictReader(f)

	for row in reader:
		
		try:
			with db.atomic():
				Assembly.create(**row)
		except Exception as e:
			if 'duplicate' in e.message:
				pass
			else:
				print e

with open('look_ups/chambers.csv', 'rU', ) as f:
	reader = DictReader(f)

	for row in reader:
		
		try:
			with db.atomic():
				Chamber.create(**row)
		except Exception as e:
			if 'duplicate' in e.message:
				pass
			else:
				print e

past_session_urls = [
	{
		  'url': 'http://www.house.mo.gov/sitemap.aspx?pid=24'
		, 'name': 'Past House Sessions'
		, 'chamber': 'H'
		, 'file_name': 'Need to regularly check: http://www.house.mo.gov/sitemap.aspx?pid=24'
	}
	, { 
		  'url': 'http://www.senate.mo.gov/pastsessions.htm'
		, 'name': 'Past Senate Sessions'
		, 'chamber': 'S'
		, 'file_name': 'Need to regularly check: http://www.senate.mo.gov/pastsessions.htm'
	  }
]

for url in past_session_urls:

	url['scheme'] = urlparse(url['url']).scheme
	url['netloc'] = urlparse(url['url']).netloc
	url['path'] = urlparse(url['url']).path
	url['params'] = urlparse(url['url']).params
	url['query'] = urlparse(url['url']).query
	url['fragment'] = urlparse(url['url']).fragment
	
	try:
		with db.atomic():
			Source_Doc.create(**url)
	except Exception as e:
		if 'duplicate' in e.message:
			pass
		else:
			print e


with open('look_ups/session_types.csv', 'rU', ) as f:
	reader = DictReader(f)

	for row in reader:
		
		try:
			with db.atomic():
				Session_Type.create(**row)
		except Exception as e:
			if 'duplicate' in e.message:
				pass
			else:
				print e


with open('look_ups/bill_types.csv', 'rU', ) as f:
	reader = DictReader(f)

	for row in reader:
		
		try:
			with db.atomic():
				Bill_Type.create(**row)
		except Exception as e:
			if 'duplicate' in e.message:
				pass
			else:
				print e

with open('look_ups/election_types.csv', 'rU', ) as f:
	reader = DictReader(f)

	for row in reader:

		try:
			with db.atomic():
				Election_Type.create(**row)
		except Exception as e:
			if 'duplicate' in e.message:
				pass
			else:
				print e

with open('look_ups/race_types.csv', 'rU', ) as f:
	reader = DictReader(f)

	for row in reader:

		try:
			with db.atomic():
				Race_Type.create(**row)
		except Exception as e:
			if 'duplicate' in e.message:
				pass
			else:
				print e