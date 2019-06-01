access_mo
=========
Access Missouri is a state government data project that provides accurate, comprehensive and up-to-date information about legislation, lawmakers and their influencers.

This repository includes the code for collecting our historic source material and parsing it into a database.

Dependencies
------------

*	[Python 2.7 +](https://www.python.org/ "Python 2.7"): An interpreted, object-oriented, high-level programming language
*	[PostgreSQL 9.3 +](http://www.postgresql.org/ "PostgreSQL"): An open source object-relational database system
*	[psycopg2](http://initd.org/psycopg/ "psycopg2"): For connecting Python to Postgres
*	[peewee](https://peewee.readthedocs.org/en/latest/): A simple object-relational mapper (ORM)
*	[requests](http://docs.python-requests.org/en/latest/ "requests"): For handling HTTP request
*	[html5lib](https://pypi.python.org/pypi/html5lib/1.0b3): For parsing HTML the same way any major browser would;
*	[beautifulsoup 4](http://www.crummy.com/software/BeautifulSoup/ "BeautifulSoup4"): For more convenient manipulation of the parsed HTML.
	
TL;DR Version
-------------

	$ psql
	# CREATE DATABASE [name of your database];
	# \q
	$ python db_setup.py [name of your database] [your Postgres user name] [your Postgres password]
	$ python load_names.py [name of your database] [your Postgres user name] [your Postgres password]
	$ python scrape_recent_elections.py [name of your database] [your Postgres user name] [your Postgres password]
	$ python get_elections_pdfs.py [name of your database] [your Postgres user name] [your Postgres password]
	$ for f in source_docs/SoS/election_results/pdfs/*; do pdftotext -enc UTF-8 -layout $f; done
	$ python prep_elec_txt.py
	$ python parse_elections.py [name of your database] [your Postgres user name] [your Postgres password]
	$ psql -U [your Postgres user name] -d [name of your database] -f sql/split_primary_races.sql
	$ psql -U [your Postgres user name] -d [name of your database] -f sql/rank_race_candidates.sql
	$ psql -U [your Postgres user name] -d [name of your database] -f sql/insert_assembly_members.sql
	$ python get_past_sessions.py [name of your database] [your Postgres user name] [your Postgres password]
	$ python get_lawmaker_profiles.py [name of your database] [your Postgres user name] [your Postgres password]
	$ python get_bill_pages.py [name of your database] [your Postgres user name] [your Postgres password]
	$ python parse_hb_sponsors.py [name of your database] [your Postgres user name] [your Postgres password]
	$ python get_sb_sponsors.py [name of your database] [your Postgres user name] [your Postgres password]
	$ python get_senate_co_sponsors.py [name of your database] [your Postgres user name] [your Postgres password]

Set up
------

First you need to set up a PostgreSQL database:

	$ psql
	# CREATE DATABASE [name of your database];
	# \q

Then, run [db_setup.py](https://github.com/gordonje/access_mo/blob/master/db_setup.py "db_setup.py"):

	$ python db_setup.py [name of your database] [your Postgres user name] [your Postgres password]

This script will create any tables not already found in the database. Each class defined in [models.py](https://github.com/gordonje/access_mo/blob/master/models.py) (other than BaseModel) maps to a table, and the attributes of each class map to columns on its table. When we eventually instantiate objects of these classes, those objects become rows in the data tables.

db_setup.py also loads records for several [look-up tables](https://github.com/gordonje/access_mo/tree/master/look_ups).

The final setup step is to run [load_names.py](https://github.com/gordonje/access_mo/blob/master/load_names.py), which will load the [female](https://github.com/gordonje/access_mo/blob/master/female_diminutives.csv) and [male](https://github.com/gordonje/access_mo/blob/master/male_diminutives.csv) formal and diminutive name combos and [known duplicate names](https://github.com/gordonje/access_mo/blob/master/known_dupes.csv). This is explained more in the next section.

Person De-Duping
----------------

A lot of the data we're collecting describes actions of specific people: when they ran for elected office, which legislative districts they've represented, bills they've sponsored and how they voted for each bill.

As is, this data doesn't include clear a representation of distinct persons. All we have to go on are person names and sometimes the chambers and districts with which they are associated. But this info comes to us in strings that take a variety of formats, even in documents coming from the same source. For example:

*	Sometimes the first name comes first, and sometimes the last name comes first;
*	Sometimes the full middle name is included, and sometimes only the middle initial is included;
*	Sometimes a formal name (e.g., Robert or Sue) is included, and sometimes a diminutive form (e.g., Bob or Sue) is used.

And this name formatting problem is complicated by the fact that parts of person's name can change completely, usually as a result of a change in marital status.

Here's how we tackle this problem.

### Parsing Name Strings

First, we have a [`parse_name()`](https://github.com/gordonje/access_mo/blob/master/model_helpers.py#L38) function in model_helpers.py, which takes a string and returns a dictionary with key / value pairs for first_name, middle_name, last_name, name_suffix, nickname and (sometimes) district.

More specifically, `parse_name()` contains definitions of these name fields in terms of regular expression patterns, and then these name field patterns are combined other regex patterns representing the name string formats found in the source documents of Access Missouri's data. The function then tries to match the provided name string to each format pattern, starting with the strictest pattern.

Within `parse_name()` we also test to make sure that the suffix didn't end up in one of the other name fields. If so, we keep trying other name formats.

parse_name() returns a dictionary with the following key/values:

*	`success`: `True` or `False`;
*	`match_pattern`: if successful, includes a description of the regex pattern to which the name string matched;
*	`name_dict`: a dictionary that includes name field key/values which have been [normalized](https://github.com/gordonje/access_mo/blob/master/model_helpers.py#L8). For example, '.' characters are removed and `None` values are replaced with empty strings, which is necessary for peewee's matching to existing records.

### Person Matching

With the name strings parsed, we can more precisely match a name to any person record we may already have.

The [`match_person()`](https://github.com/gordonje/access_mo/blob/master/model_helpers.py#L133) function in model_helpers.py takes the parsed name fields as its arguments, then queries to find an existing person with same combination of name field values.

Actually, `match_person()` runs as many as many as 10 queries in order to compensate for inconsistencies in the name formats and `parse_name()` results. As soon as one of the queries returns only one person record, match_person() returns that Person object with a found value of `True`. If none of the queries return only one result, it returns `False`.

Luckily with this data set, we're dealing with a relatively small number of distinct persons: At most, only about 3,000. So our matching rules can be rather liberal in terms of combining similar records. For the more ambiguous cases, we've added queries to check for case when we might have incorrectly conflated records.

The specific duplicate scenarios we're accounting for are:

#### Extraneous Last Name Characters

Some people have multi-word last names, and sometimes that includes extraneous characters like ' ' or '-', sometimes not. For example, these three records:

	first_name | middle_name | last_name      | name_suffix 
	-----------+-------------+----------------+-------------
	Yaphett    |             | El-Amin        |             
	Yaphett    |             | ElAmin         |             
	Yaphett    |             | El Amin        |             

Should become a single person record. 

#### Concatenate Middle and Last Names

When parsing the name strings, we can't always confidentially distinguish between a middle name and multi-part last name. As such, we end up with cases like the following:

	first_name | middle_name | last_name      | name_suffix 
	-----------+-------------+----------------+-------------
	Sharon     | Sanders     | Brooks         |             
	Sharon     |             | Sanders Brooks |             
	Robin      | Wright      | Jones          |             
	Robin      |             | Wright-Jones   |             

Which should be two person, not four. 

#### Same Middle Initial

We also assume that combinations of first name, middle initial, last name and name suffix should be a distinct person. For example, these records:

	first_name | middle_name | last_name      | name_suffix 
	-----------+-------------+----------------+-------------
	Jason      | G           | Crowell        |             
	Jason      | Glennon     | Crowell        |             

Should become a single person record. 

This scenario is ambiguous in that records could have the same middle initial but different middle names. For example, we don't want to treat Jason Glennon Crowell and Jason Garrett Crowell as the same person. 

We can check for these cases by running [this `SELECT`](https://github.com/gordonje/access_mo/blob/master/sql/check_distinct_middle_names.sql) which counts the number of middle names for each first, last and suffix group. If the query doesn't return any results, then we're good.

#### Same First Name, Last Name and Name Suffix

We also combine records with no middle name value with records that have the same first name, last name and name suffix values. For example, these records:

	first_name | middle_name | last_name      | name_suffix 
	-----------+-------------+----------------+-------------
	Galen      |             | Higdon         | Jr          
	Galen      | Wayne       | Higdon         | Jr          

Should become a single person.

This is another ambiguous scenario. Say there was an additional record -- Galen Henry Higdon Jr. -- then the record lacking a middle name could match to either Galen Higdon Jr. that does.

We can check for these cases by running [this `SELECT`](https://github.com/gordonje/access_mo/blob/master/sql/check_distinct_middle_initials.sql)) which counts the number of distinct middle initials for each first name, last name and name suffix and joins back to person name records lacking a middle name. If the query doesn't return any results, then we're good.

#### Concatenate First and Middle Names

Next, we combine records like these:

	first_name | middle_name | last_name      | name_suffix 
	-----------+-------------+----------------+-------------
	J          | C           | Kuessner       |             
	JC         |             | Kuessner       |             

Where the person's first name is basically his first and middle initials. Put it another way, we're combining cases where the concatenation of the first name and middle name values are the same for each last name / name suffix combo. 

#### First Name Matches Middle Name

We also combine records where the last name and name suffix are the same and the first name matches the middle name. For example, these four records:

	first_name | middle_name | last_name      | name_suffix 
	-----------+-------------+----------------+-------------
	W          | Todd        | Akin           |             
	Todd       |             | Akin           |
	Gail       | McCann      | Beatty         |             
	E          | Gail        | Beatty         |             

Should become two person records. 

This second pair is a little suspect, but according to a [Missouri Times Q-and-A](http://themissouritimes.com/7215/five-questions-rep-gail-mccann-beatty-d-kansas-city/) from 2013, Gail McCann Beatty ran in the 1999 special election for the 43rd House District to which E Gail Beatty is assigned. 

#### First Name Matches Nickname

We also combine records where the first name matches the nickname for a given last name / name suffix combo. For example, these records:

	first_name | last_name   | name_suffix | nickname 
	-----------+-------------+-------------+----------
	Anthony    | Leech       |             | Tony     
	Tony       | Leech       |             |          

Should become a single person.

#### Formal Name Matches Diminutive First Name

Related to the previous scenario, we also combine records where the first name is the diminutive form of a formal name for a given last name / name suffix combo. For example, these 5 records:

	first_name | middle_name | last_name      | name_suffix 
	-----------+-------------+----------------+-------------
	Kenneth    |             | Jones          |             
	Kenny      |             | Jones          |             
	Ken        |             | Jones          |             
	Charlie    |             | Schlottach     |             
	Charles    | W           | Schlottach     |             

Should become 2 distinct persons.

For this scenario, we're pulling in some outside help. This [repo](https://github.com/dtrebbien/diminutives.db) includes two .csv files of formal names and their diminutives, one for female names and one for male names. The [load_names.py](https://github.com/gordonje/access_mo/blob/master/load_names.py) script from the setup steps imports these names into the `formal_name` and `diminutive_name` so that we can test if a provided first name is either a formal name with diminutives or is a diminuitive of a formal name. If either of these is true, then we can incorporate these alternative first names into our first name queries accordingly.

#### Known Dupes

Even after all that work, there are potentially still duplicate person records that can't be handled programmatically, such as when a person's last name changes completely (probably as a result of marriage or divorce). For example, after a research, we learned that these records:

	first_name | middle_name | last_name      | name_suffix 
	-----------+-------------+----------------+-------------
	Linda      |             | Black          |             
	Linda      | R           | Fischer        |             

Actually represent [one person](http://house.mo.gov/member.aspx?year=2014&district=117).

We deal with these known dupes by mapping these alternate names to distinct person record names in the [known_dupes.csv](https://github.com/gordonje/access_mo/blob/master/sql/known_dupes.csv), which is imported by the [load_names.py](https://github.com/gordonje/access_mo/blob/master/load_names.py) script as part of the setup process.

Here's one set of records that might require further research:

	first_name | middle_name | last_name      | name_suffix 
	-----------+-------------+----------------+-------------
	John       | L           | Bowman         |             
	John       | L           | Bowman         | Jr          
	John       | L           | Bowman         | Sr          

There might be two John L Bowman, but there probably aren't three, and there's no clear path to map the related race_candidate records to the correct John L Bowman. We'll have to come back to this one.

### Storing Person and Person_Names

The `person` table contains distinct combinations of first_name, middle_name, last_name and name_suffix. Access Missouri considers these records to represent distinct persons that have run for and served in office.

Every variation of each distinct person's name has been found by our parsing and matching process is stored in the `person_name` table.

So whenever we encounter a name string, after parsing it into name fields, we take the following steps that resulting in either getting or creating a `person` record:

1.	Query to see if the given combination of first / middle / last / suffix is already in the `person` table;
2.	If not, query to see if the given combination of first / middle / last / suffix is already in the `person_name` table;
3.	If not, call `match_person()` which execute multiple queries to find a person that meets one of the rules [described above](#person-matching).
4.	If not, then create a new person record.

If we do match to an existing person, then we may also update the middle name and name suffix values if the new name values are more complete than the stored name's values.

All of this logic is encapsulated in ['get_or_create_person()'](https://github.com/gordonje/access_mo/blob/master/model_helpers.py#L378).

Election Results
----------------

Access Missouri currently includes the results of each election going back to the 1996 General Election. Compared to the lawmaker profiles found on the House and Senate Clerk websites, the House and Senate race results are more precise and complete sources of information about which persons have served in which legislative offices.

Results for the elections that occurred from 2012 through 2014 are avaiable on [here](http://enrarchives.sos.mo.gov/enrnet/Default.aspx) on the Missouri Secretary of State's website. Run [scrape_recent_elections.py](https://github.com/gordonje/access_mo/blob/master/scrape_recent_elections.py) to gather, parse and write these records to the database.

Results for the elections that occurred from 1995 to through 2014 are only available [here](http://s1.sos.mo.gov/elections/resultsandstats/previousElections) in .pdf format. So to getting these results requires extra steps:

1.	Download the .pdfs:

		$ python get_elections_pdfs.py

2.	Extract the text from the .pdfs:

		$ for f in past_content/SoS/election_results/pdfs/*; do pdftotext -enc UTF-8 -layout $f; done

3.	Remove extraneous unicode characters from the /txt files (specifically `\x0c` and `\xa0`) and move them into their own directory:

		$ python prep_elec_txt.py

4.	Parse the text and save records to the database:

		$ python parse_elections.py [name of your database] [your Postgres user name] [your Postgres password]	

Both processes -- scraping recent elections and parsing past elections -- add the following records to the database:

1.	Elections, including the election date and type (i.e., General, Primary or Special);
	1.	To each general and special election, we also assign and assembly_id, referencing the general assembly to which the winning candidate was elected;
2.	Races, including the type (i.e., State House or State Senate) and the legislative district;
3.	Persons, which includes any combination of first name, middle name, last name and name suffix found among the candidates listed for each election. These records will subsequently be de-duped to distinct person records;
4.	Person_Names, which includes any combination or person name fields as well as nickname;
5.	Race_Candidate, including the id of the person who ran in the race, their party, the number of votes received and the percentage of total votes received.

At this point, the primary races are conflated. That is, for each primary election, the Republican candidates and the Democratic candidates are listed as running in a single race. In reality, though, primary candidates from different parties aren't competing against each other (not yet, anyway). So we need to split up primary candidates into separate races for their respective parties:

	$ psql -U [your Postgres user name] -d [name of your database] -f sql/split_primary_races.sql 

Then, we also rank the candidates in each race according to the votes each received as a percent of the total votes cast in each race. The rank 1 candidates were the winners of each race:

	$ psql -U [your Postgres user name] -d [name of your database] -f sql/rank_race_candidates.sql 

Recall that our general and special election records reference the assembly to which each winning candidate was elected. So finally, we can insert assembly member records, denoting which person represented which chamber and district in which assembly. 

We also have to insert additional assembly member records for senators, who are elected for four year terms (i.e., two general assemblies). 

These `INSERT` commands are in [insert_assembly_members.sql](https://github.com/gordonje/access_mo/blob/master/sql/insert_assembly_members.sql). Note that a few of the Senators elected via special election have to be handled individually.

Getting Session Data
--------------------

Access Missouri currently includes legislative data from each session going back to the first Regular Session of the 88th General Assembly in 1995.

The House and Senate Clerks have two distinct websites that publish this information.

Here are the current commands to run (in order):

1.	Run get_past_sessions.py
2.	Run get_lawmaker_profiles.py
3.	Run get_bill_pages.py
4.	Run parse_hb_sponsors.py
5.	Run parse_sb_sponsors.py
6.	Run get_sb_co_sponsors.py

