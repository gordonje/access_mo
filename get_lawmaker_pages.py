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
								Source_Page.chamber.desc(), Source_Page.year.desc()
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

	members = []

	if member_page.chamber == 'H':

		if member_page.year > 2001:
			soup = BeautifulSoup(content, 'lxml')
		elif member_page.year <= 2001:
			soup = BeautifulSoup(content, 'html5lib')

		if member_page.year > 2010:

			for tr in soup.find(id = 'ContentPlaceHolder1_gridMembers_DXMainTable').find_all('tr')[1:]:

				tds = tr.find_all('td')

				members.append({
					  'last': tds[0].text.strip()
					, 'first': tds[1].text.strip()
					, 'district': tds[2].text.strip()
					, 'party': tds[3].text.strip()
					, 'year': member_page.year
					, 'chamber': member_page.chamber
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

					members.append({
						  'last': last
						, 'first': first
						, 'middle': middle
						, 'district': tds[1].text.split('-')[0].strip()
						, 'party': tds[1].text.split('-')[1].strip()
						, 'year': member_page.year
						, 'chamber': member_page.chamber
						, 'url': tds[0].find('a')['href']
					})

	if member_page.chamber == 'S':

		soup = BeautifulSoup(content, 'lxml')

		if member_page.year > 2004:

			for tr in soup.find('table', attrs = {'border': 0, 'width': re.compile('[6,9]0%')}).find_all('tr'):
				tds = tr.find_all('td')

				try:
					tds[0].find('a')['href']
				except:
					pass
				else:

					name = tds[0].text.strip().split()

					if 'Vacant' not in name:

						last = name.pop(-1)
						first = name.pop(0)

						try:
							middle = name.pop()
						except:
							middle = None

						p_d = tds[1].text.strip().split('-')

						party = p_d[0]
						district = p_d[1]

					else:
						first = 'Vacant'
						middle = 'Vacant'
						last = 'Vacant'
						party = None
						district = tds[1].text.strip()

						if len(district) == 0:
							district = name.pop(-1)

					members.append({
						  'last': last
						, 'first': first
						, 'middle': middle
						, 'district': district
						, 'party': party
						, 'year': member_page.year
						, 'chamber': member_page.chamber
						, 'url': tds[0].find('a')['href']
					})

		elif 2000 < member_page.year & member_page.year <= 2004  :

			for link in soup.find_all('a'):

				if link.find_parent('td'):

					name = link.text.strip().split()

					p_d = link.find_parent('td').find_next_sibling('td').text.strip().split('-')

					if 'Vacant' not in name:

						last = name.pop(-1)
						first = name.pop(0)

						try:
							middle = name.pop()
						except:
							middle = None

						party = p_d[0]
						district = p_d[1]

					else:
						first = 'Vacant'
						middle = 'Vacant'
						last = 'Vacant'
						party = None
						district = p_d[0]

					members.append({
						  'last': last
						, 'first': first
						, 'middle': middle
						, 'district': district
						, 'party': party
						, 'year': member_page.year
						, 'chamber': member_page.chamber
						, 'url': link['href']
					})

		else:

			for link in soup.find_all('a'):

				if '/index' not in link['href']:

					name = [ i for i in link.text.strip().split() if not i.startswith('Senator')]

					if 'Vacant' not in name:

						last = name.pop(-1)
						first = name.pop(0)

						try:
							middle = name.pop()
						except:
							middle = None

					else:
						first = 'Vacant'
						middle = 'Vacant'
						last = 'Vacant'

					parent_url_path = re.search('^.+\.gov\/.+\/', member_page.url).group()

					if member_page.url not in link['href']:
						member_url = parent_url_path + link['href']
					else:
						member_url = link['href']
					
					members.append({
						  'last': last
						, 'first': first
						, 'middle': middle
						, 'district': re.search('mem(\d+).htm', link['href']).group(1)
						, 'party': None
						, 'year': member_page.year
						, 'chamber': member_page.chamber
						, 'url': member_url
					})

	for member in members:

		if member['chamber'] == 'H':
			if member['year'] >= 2009:
				member['url'] = 'http://house.mo.gov/member.aspx?year={0}&district={1}'.format(member['year'], member['district'])

		source_page = {
			  'year': member['year']
			, 'chamber': member['chamber']
			, 'scheme': urlparse(member_page.url).scheme
			, 'netloc': urlparse(member_page.url).netloc
			, 'path': urlparse(member['url']).path
			, 'params': urlparse(member['url']).params
			, 'query': urlparse(member['url']).query
			, 'fragment': urlparse(member['url']).fragment
			, 'url': urlunparse((
					  urlparse(member_page.url).scheme
					, urlparse(member_page.url).netloc
					, urlparse(member['url']).path
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
		except Exception, e:
			print e
			r_sesh = session()
			get_content(sp_obj, r_sesh)

print 'fin.'

