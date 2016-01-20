
import re
import io
import os

base_path = 'source_docs/SoS/election_results/'

if not os.path.exists(base_path + 'txts/'):
	os.makedirs(base_path + 'txts/')

for i in os.listdir(base_path + 'pdfs/'):

	if '.txt' in i:

		print '   Prepping {}...'.format(i)

		with io.open(base_path + 'pdfs/' + i, mode = 'r', encoding='UTF-8') as old:

			with io.open(base_path + 'txts/' + i, mode = 'w', encoding='UTF-8') as new:
			
				new.write(old.read().replace(u'\x0c', '').replace(u'\xa0', ' '))

		os.remove(base_path + 'pdfs/' + i)

print 'fin.'