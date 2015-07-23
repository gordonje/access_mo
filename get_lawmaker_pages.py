import os
from utils import *

parent = Source_Page.alias()

for member_page in Source_Page.select(
								Source_Page, parent
							).join(
								parent, on=(Source_Page.parent_id == parent.id).alias('parent')
							).where(
								(Source_Page.name.contains('Roster')|Source_Page.name.contains('Senators'))
								& ~(parent.name.contains('Extraordinary'))
							).order_by(
								Source_Page.chamber, Source_Page.year.desc()
							):


	print '   Getting members for {0} {1} {2}...'.format(member_page.chamber, member_page.year, member_page.parent.name)

	directory = 'past_content/{0}/{1}_{2}/members'.format(member_page.chamber, member_page.year, member_page.parent.name.replace(' ', '_')) 
	
	if not os.path.exists(directory):
		os.makedirs(directory)

	try:
		content = get_content(member_page, r_sesh)
	except: # needs to be more specific
		r_sesh = session()
		content = get_content(member_page, r_sesh)

	if member_page.year > 2001:
		soup = BeautifulSoup(content, 'lxml')
	elif member_page.year <= 2001:
		soup = BeautifulSoup(content, 'html5lib')

	members = []

	if member_page.chamber == 'H':

		if member_page.year > 2010:

			for tr in soup.find(id = 'ContentPlaceHolder1_gridMembers_DXMainTable').find_all('tr')[1:]:

				tds = tr.find_all('td')

				member_url = tds[0].find('a')['href']

				parent_path = urlparse(member_page.url).path

				if parent_path not in member_url:
					full_path_url = parent_path + member_url
				else:
					full_path_url = member_url

				members.append({
					  'last': tds[0].text.strip()
					, 'first': tds[1].text.strip()
					, 'district': tds[2].text.strip()
					, 'party': tds[3].text.strip()
					, 'year': member_page.year
					, 'chamber': member_page.chamber
					, 'url': full_path_url
				})

		if member_page.year <= 2010:

			if member_page.year == 1998:
				trs = soup.find('table', attrs = {'border': 2, 'width': '80%'}).find_all('tr')
			else:
				trs = soup.find('table', attrs = {'border': 2, 'width': '100%'}).find_all('tr')

			for tr in trs:
				tds = tr.find_all('td')

				try:
					tds[0].find('a')['href']
				except:
					pass
				else:
					name = tds[0].text.strip().split()

					last = name.pop(-1)
					first = name.pop(0)

					try:
						middle = name.pop()
					except:
						middle = None

					member_url = tds[0].find('a')['href']

					parent_url = urlparse(member_page.url).netloc

					if parent_path not in member_url:
						full_path_url = parent_path + member_url
					else:
						full_path_url = member_url

					members.append({
						  'last': last
						, 'first': first
						, 'middle': middle
						, 'district': tds[1].text.split('-')[0].strip()
						, 'party': tds[1].text.split('-')[1].strip()
						, 'year': member_page.year
						, 'chamber': member_page.chamber
						, 'url': full_path_url
					})

	# if member_page.chamber == 'S': ....

	for member in members:

		print member_page.url
		print member['url'] 

		print '---------------------------------------'


		source_page = {
			  'year': member['year']
			, 'chamber': member['chamber']
			, 'scheme': urlparse(member_page.url).scheme
			, 'netloc': urlparse(member_page.url).netloc
			, 'path': urlparse(member['url']).path.replace('./', '/')
			, 'params': urlparse(member['url']).params
			, 'query': urlparse(member['url']).query
			, 'fragment': urlparse(member['url']).fragment
			, 'url': urlunparse((
					  urlparse(member_page.url).scheme
					, urlparse(member_page.url).netloc
					, urlparse(member['url']).path.replace('./', '/')
					, urlparse(member['url']).params
					, urlparse(member['url']).query
					, urlparse(member['url']).fragment
				))
			, 'name': '{0} {1}'.format(member['first'], member['last'])
			, 'file_name': '{0}/{1}.html'.format(directory, member['district'])
			, 'parent_id': member_page.parent_id
		}

		try:
			with db.atomic():
				sp_obj = Source_Page.get_or_create(**source_page)[0]
		except Exception, e:
			print e

		member['source_page'] = sp_obj.id

		member['person'] = Person.get_or_create(
				  first_name = member['first']
				, last_name = member['last']
			)[0]

		if member['year'] % 2 == 0:
			member['assembly'] = Assembly.get(Assembly.end_year == member['year'])
		else:
			member['assembly'] = Assembly.get(Assembly.start_year == member['year'])

			try:
				with db.atomic():
					Legislator_Assembly.create(**member)
			except IntegrityError:
				pass

		try:
			get_content(sp_obj, r_sesh)
		except:
			print '      Lost connection, resetting session...'
			r_sesh = session()

print 'fin.'

