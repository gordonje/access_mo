from models import *
import csv

with open('female_diminutives.csv', 'rU') as f:
	reader = csv.reader(f)

	for row in reader:
		with db.atomic():
			f_n = Formal_Name.create_or_get(name = row[0])[0]

		for i in row[1:]:
			with db.atomic():
				Diminutive_Name.create_or_get(
					  formal_name = f_n
					, name = i
					, sex = 'F'
				)

with open('male_diminutives.csv', 'rU') as f:
	reader = csv.reader(f)

	for row in reader:

		with db.atomic():
			f_n = Formal_Name.create_or_get(name = row[0])[0]

		for i in row[1:]:
			try:
				with db.atomic():
					Diminutive_Name.create(
						  formal_name = f_n
						, name = i
						, sex = 'M'
					)

			except Exception as e:
				if 'duplicate' in e.message:

					diminutive = Diminutive_Name.get(
										  Diminutive_Name.formal_name == f_n
										, Diminutive_Name.name == i
									)
					
					diminutive.sex = 'N'

					with db.atomic():
						diminutive.save()

				else:
					print e
