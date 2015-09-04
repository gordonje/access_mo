# -*- coding: utf-8 -*-

import os
from models import *
import re
import io
import inspect

f_path = 'past_content/SoS/txt_files/'

# select the race_types into a list of matching purposes
race_types = []

for race_type in Race_Type.select():
	race_types.append(race_type)

# election date pattern
date_pattern = re.compile("^\s*(\w+,\s\w+\s\d{2},\s\d{4})$")

# candidate match pattern
cand_pattern = re.compile("^\s+(\w[\w\.\s,\xad'\(\)]+)\s{2,}([A-Za-z\d]{2,3})\s+([\d,]+)\s+([\d\.%]+)\s*$")

# name suffix pattern
suffix_pattern = re.compile(' (Jr\.|Sr\.)')

# candidate name parsing patterns (see this regex in action here: http://regexr.com/3bmnl)
first_last_pattern = re.compile("^(?P<first>[\w\xad'\.]+) (?:(?P<middle>[\w\xad'\.]+) )?(?P<last>[\w\xad '\.]+)$")
last_first_pattern = re.compile("(?P<last>[\w\xad '\.]+)(?:,? (?P<suffix1>Jr\.|Sr\.|[IV]+))?, (?P<first>[\w\.]+)(?: (?P<middle>[\w\.]+))?(?: \((?P<nickname>.+)\))?(?: (?P<suffix2>Jr\.|Sr\.|[IV]+))?")

elections = []

# loop over the files in the SoS/txt_files folder...
for i in os.listdir(f_path):
	# skipping this system file
	if i != '.DS_Store':

		# print '   Getting election data from {}'.format(i)

		# set up an election for each file
		election = Election(
			  file_name = f_path + i
			, date = None
			, races = []
		)

		print election.file_name

		# determine which type of election it is (based on file name)
		for elec_type in Election_Type.select():
			if elec_type.name in i:
				election.election_type = elec_type

		# open the file
		with io.open(f_path + i, mode = 'r', encoding='UTF-8') as f:

			# declare a line reader so that we can reference line numbers (i.e., index position)
			reader = f.readlines()
			
			# for each line in the file
			for idx, line in enumerate(reader):

				# ignore lines with only one non-whitespace character
				if len(line.strip()) > 1:

					date_match = re.match(date_pattern, line)
					cand_match = re.match(cand_pattern, line)

					# if the line matches the election date pattern...
					if date_match != None:

	 					# set this election attribute
						election.election_date = date_match.group(1)

	 				# see if any of the race types names are in the line
					elif any(race_type.name in line for race_type in race_types):

						# if so, then set up a new race
						race = Race(
							  candidates = []
							, total_votes = None
						)

						# set which type of race it is
						for race_type in race_types:
							if race_type.name in line:
								# then set this attribute
								race.race_type = race_type.id

						# if the candidate line also contains the word 'District'...
						if 'District' in line:
							# try finding the district number and setting this attribute
							try:
								race.district = re.search('\d+', line).group()
							except AttributeError:
								print 'No district number'
								print repr(line)

					# if the line matches the candidate pattern
					elif cand_match != None:

						# append a candidate to the race's list
						race.candidates.append(
							Race_Candidate(
								  raw_name = cand_match.group(1).strip()
								, party = cand_match.group(2).strip()
								, votes = cand_match.group(3).strip().replace(',', '')
								, pct_votes = cand_match.group(4).replace('%', '').strip()
							)
						)

					# if the phrase 'Total Votes' is in the line
					elif 'Total Votes' in line:
						# search the current line for the total votes number
						try:
							race.total_votes = re.search('[\d|,]+', line).group().replace(',', '')						
						# if not founnd, try the next line
						except AttributeError:						
							race.total_votes = re.search('[\d|,]+', reader[idx + 1]).group().replace(',', '')
						
						
						# after getting the total votes, append the race to the election's list 
						election.races.append(race)

					# other wise print the line to see what we might be missing
					else:						
						print repr(line)

		elections.append(election)

		print '=============='

for election in elections:

	try:
		with db.atomic():
			election.save()
	except Exception as e:
		if 'duplicate' in e.message:
			pass
		else:
			print 'Error on line #{0}: {1}'.format(inspect.currentframe().f_lineno, e)

	for race in election.races:
		# for now, only focus on the state legislative races
		if 'State Senator' in race.race_type.name or 'State Representatives' in race.race_type.name:

			race.election = election.id

			try:
				with db.atomic():
					race.save()
			except Exception as e:
				if 'duplicate' in e.message:
					pass
				else:
					print 'Error on line #{0}: {1}'.format(inspect.currentframe().f_lineno, e)

			for candidate in race.candidates:

				candidate.race = race.id

				raw_name = candidate.raw_name

				suffix_match = re.search(suffix_pattern, raw_name)

				if suffix_match != None:
					candidate.name_suffix = suffix_match.group(1)
					raw_name = re.sub(suffix_pattern, '', raw_name).replace(',,', ',')

				# if the candidate's raw name includes a comma, then use the last name, first name pattern
				if ',' in raw_name:
					parse_dict = re.match(last_first_pattern, raw_name).groupdict()

					candidate.first_name = parse_dict['first']
					candidate.middle_name = parse_dict['middle']
					candidate.last_name = parse_dict['last']
					candidate.nickname = parse_dict['nickname']

				# # otherwise use the first name last name pattern
				else:
					parse_dict = re.match(first_last_pattern, raw_name).groupdict()

					candidate.first_name =  parse_dict['first']
					candidate.middle_name =  parse_dict['middle']
					candidate.last_name =  parse_dict['last']

				try:
					with db.atomic():
						candidate.save()
				except Exception as e:
					if 'duplicate' in e.message:
						pass
					else:
						print 'Error on line #{0}: {1}'.format(inspect.currentframe().f_lineno, e)

