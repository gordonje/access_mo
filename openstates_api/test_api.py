
from config import key
import requests
import json

os_bill_id = 'MOB00003794'

url = 'http://openstates.org/api/v1/bills/{0}/?apikey={1}'.format(os_bill_id, key)

response = requests.get(url)

json_results = response.json()

for action in json_results['actions']:
	print action

with open('results.json', 'wb') as out_file:
	out_file.write(response.content)
