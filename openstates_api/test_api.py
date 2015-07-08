
from config import key # save a file named config.py that contains key = [whatever your key OS sends you]
import requests
import csv

os_bill_id = 'MOB00003794'

url = 'http://openstates.org/api/v1/bills/{0}/?apikey={1}'.format(os_bill_id, key)

response = requests.get(url)

results = response.json()

with open('results.csv', 'wb') as csv_out:

	fields = list(results['actions'][0].viewkeys())
	writer = csv.DictWriter(csv_out, fieldnames = fields)

	writer.writeheader()

	for action in results['actions']:
		print action
		writer.writerow(action)

with open('results.json', 'wb') as json_out:
	json_out.write(response.content)
