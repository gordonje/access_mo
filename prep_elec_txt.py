
import re
import io
import os

f_path = 'past_content/SoS/'

if not os.path.exists(f_path + 'txt_files/'):
	os.makedirs(f_path + 'txt_files/')

for i in os.listdir(f_path):

	if '.txt' in i:

		print '   Prepping {}...'.format(i)

		with io.open(f_path + i, mode = 'r', encoding='UTF-8') as old:

			with io.open(f_path + 'txt_files/' + i, mode = 'w', encoding='UTF-8') as new:
			
				new.write(old.read().replace(u'\x0c', '').replace(u'\xa0', ' '))

		os.remove(f_path + i)		

print 'fin.'