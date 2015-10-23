from models import *
from csv import DictReader

id = 1

with open('name_groups.tsv', 'rU') as f:
	reader = DictReader(f, delimiter='\t')

	for row in reader:

		try:
			with db.atomic():
				Name_Group.create(group_id = id, name = row['formal_name'], name_type = 'FORM', sex = row['sex'])
		except Exception as e:
			print e

		dimin_list = row['diminutive_names'].split(',')

		for dimin in dimin_list:
			try:
				with db.atomic():
					Name_Group.create(group_id = id, name = dimin, name_type = 'DIMN', sex = row['sex'])
			except Exception as e:
				print e

		id += 1
