#!/usr/bin/env python
# -*- coding: utf-8 -*-

from models import *
from urlparse import urlparse
import csv

db.create_tables([
				  Assembly
				, Chamber
				, Person
				, Session_Type
				, Session
				, Source_Doc
				, Assembly_Member
				, District_Vacancy
				, Bill_Type
				, Bill
				, Bill_Cosponsor
				# , Bill_Amendment
				, Bill_Action
				, Bill_Summary
				, Bill_Text
				, Bill_Topic
				, Committee
				, Committee_Member
			], True)


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
	except Exception, e:
		print e


with open('look_ups/session_types.csv', 'rU', ) as f:
	reader = csv.DictReader(f)

	for row in reader:
		
		try:
			with db.atomic():
				Session_Type.create(**row)
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
			print 'Error when making bill type'
			print e

