access_mo
=========
Access Missouri is a state government data project that provides accurate, comprehensive and up-to-date information about legislation, lawmakers and their influencers.

This repository includes the code for collecting our source material and building our database.

Dependencies
------------

*	[Python 2.7 +](https://www.python.org/ "Python 2.7"): An interpreted, object-oriented, high-level programming language
*	[PostgreSQL 9.3 +](http://www.postgresql.org/ "PostgreSQL"): An open source object-relational database system
*	[psycopg2](http://initd.org/psycopg/ "psycopg2"): For connecting Python to Postgres
*	[peewee](https://peewee.readthedocs.org/en/latest/): A simple object-relational mapper (ORM)
*	[requests](http://docs.python-requests.org/en/latest/ "requests"): For handling HTTP request
*	[beautifulsoup 4](http://www.crummy.com/software/BeautifulSoup/ "BeautifulSoup4"): For parsing HTML into navigable strings

Set up
------

First you need to set up a local PostgreSQL database:

	$ psql
	# CREATE DATABASE [name of your database];
	# \q

Then, run [db_setup.py](https://github.com/gordonje/access_mo/blob/master/db_setup.py "db_setup.py"):

$ python db_setup.py [name of your database] [your Postgres user name] [your Postgres password]

This script will create any tables not already found in the database. Each class defined in [models.py](https://github.com/gordonje/access_mo/blob/master/models.py) (other than BaseModel) maps to a table, and the attributes of each class map to columns on its table. When we eventually instantiate objects of these classes, those objects become rows in the data tables.

Election Results
----------------

Access Missouri currently includes the results of each State Senate and State House race since the 1996 General Election. Compared to the lawmaker profiles found on the House and Senate Clerk websites, these elections results are a more precise and complete source of information about which persons have served in which legislative offices.

Results for the elections that occurred from 2012 through 2014 are avaiable on [here](http://enrarchives.sos.mo.gov/enrnet/Default.aspx) on the Missouri Secretary of State's website. Run [scrape_recent_elections.py](https://github.com/gordonje/access_mo/blob/master/scrape_recent_elections.py) to gather, parse and write these records to the database.

Results for the elections that occurred from 1995 to through 2014 are only available [here](http://s1.sos.mo.gov/elections/resultsandstats/previousElections) in .pdf format. So to getting these results requires extra steps:

1.	Download the .pdfs:

		$ python get_elections_pdfs.py

2.	Extract the text from the .pdfs:

		$ for f in past_content/SoS/election_results/pdfs/*; do pdftotext -enc UTF-8 -layout $f; done

3.	Remove extraneous unicode characters from the /txt files (specifically \x0c and \xa0) and move them into their own directory:

		$ python prep_elec_txt.py

4.	Parse the text and save records to the database:

		$ python parse_elections.py [name of your database] [your Postgres user name] [your Postgres password]	

Both process -- scraping recent elections and parsing past elections -- add the following records to the database:

1.	Elections, including the election date and type (i.e., General, Primary or Special);
	1.	To each general and special election, we also assign and assembly_id, referencing the general assembly to which the winning candidate was elected;
2.	Races, including the type (i.e., State House or State Senate) and the legislative district;
3.	Persons, which includes any combination of first name, middle name, last name and name suffix found among the candidates listed for each election. These records will subsequently be de-duped to distinct person records;
4.	Person_Names, which includes any combination or person name fields as well as nickname;
5.	Race_Candidate, including the id of the person who ran in the race, their party, the number of votes received and the percentage of total votes received.

At this point, the primary races are conflated. That is, for each primary election, the Republican candidates and the Democratic candidates are listed as running in a single race. In reality, though, primary candidates from different parties aren't competing against each other (not yet, anyway). So we need to split up primary candidates into separate races for their respective parties:

	$ psql -U [your Postgres user name] -d [name of your database] -f sql/split_primary_races.sql 

Finally, we also rank the candidates in each race according to the votes each received as a percent of the total votes cast in each race. The rank 1 candidates were the winners of each race:

	$ psql -U [your Postgres user name] -d [name of your database] -f sql/.sql 

Person De-Duping
----------------

Access Missouri's analysis and infographics require us to model distinct persons, which races they've run in and which offices they've held. While there isn't a readily available source for this exact information, we are able to extrapolate it from the SoS election results.

As we processed the election results, we used regular expression patterns to parse race candidate names into their constitute parts: first name, middle name (or initial), last name, name suffix and nickname. We then wrote the distinct combinations of first name, middle name, last name and name suffix values into the Persons table, and wrote these combinations, plus any nicknames found with them into the Person_Names table. 

But formats for candidate names have varied widely over the years: Sometimes they include a full middle name, sometimes they only include a middle initial; sometimes they use the candidates formal name (e.g., Robert or Sue) and sometimes they include the diminutive forms (e.g., Bob or Sue).

Moving forward from here, we need to remove duplicate person records while ensuring that these supposedly distinct persons are referenced by the person_name and race_candidate records. More specifically, for each de-duping rule we adopt we need to:

1.	Update race_candidate.person_id to the lowest person_id value;
2.	Update person_name.person_id to the lowest person_id value;
3.	Update the related name fields of the person record so that the distinct person record is complete
4.	Delete any leftover person records without any related person_names records

### Dedupe Persons: Extraneous Last Name Characters

We'll start off using the most conservative definition of person, that is, distinct combinations of first name, middle name, last name and name suffix. In some cases, last names contain extraneous characters, like a space or a hyphen, though the SoS results may not have consistently published them. For example, these three records:

	first_name | middle_name | last_name      | name_suffix 
	-----------+-------------+----------------+-------------
	Yaphett    |             | El-Amin        |             
	Yaphett    |             | ElAmin         |             
	Yaphett    |             | El Amin        |             

Should become a single person record. 

PostgreSQL has convenient [regex functionality](http://www.postgresql.org/docs/9.4/static/functions-matching.html) that will help with this task (one of the many reasons it is our favorite relational database manager). We just need to run [these UPDATE and DELETE](https://github.com/gordonje/access_mo/blob/master/sql/dedupe_on_extra_last_name_chars.sql) commands.

### Dedupe Persons: Same Middle Initial

Second, we are going to assume that combinations of first name, middle initial, last name and name suffix should be a distinct person. For example, these records:

	first_name | middle_name | last_name      | name_suffix 
	-----------+-------------+----------------+-------------
	Jason      | G           | Crowell        |             
	Jason      | Glennon     | Crowell        |             

Should become a single person record. 

This step assumes that, for example, there isn't also a Jason Garrett Crowell in our records. But we can check this by making sure there isn't more than one middle name value with two or more characters for any combination of first name, last name and name suffix. So as long as [this SELECT](https://github.com/gordonje/access_mo/blob/master/sql/check_distinct_middle_names.sql) doesn't return any records, we are safe to run [these UPDATE and DELETE](https://github.com/gordonje/access_mo/blob/master/sql/dedupe_on_middle_initial.sql) commands.

### Deduping Persons: Same First Name, Last Name and Name Suffix

Next, we combine persons that have the same first name, last name and name suffix and either no middle name value or some middle name value. For example, these records:

	first_name | middle_name | last_name      | name_suffix 
	-----------+-------------+----------------+-------------
	Galen      |             | Higdon         | Jr          
	Galen      | Wayne       | Higdon         | Jr          

Should become a single person.

This step assumes that a combination of first name, last name and name suffix represent a distinct person, irrespective of the middle name value. In the previous deduping step, we confirmed that each combo of first / middle / suffix have multiple full middle names. Now we should check that each combo of first / middle / suffix doesn't have multiple middle initals by running [this query](https://github.com/gordonje/access_mo/blob/master/sql/check_distinct_middle_initials.sql).

Turns out there are two. But according to their respective legislative profiles, there's likely really only one [Rita Days](http://www.senate.mo.gov/06info/members/bios/bio14.htm) and one [Linda Black Fischer](http://house.mo.gov/member.aspx?year=2014&district=117). So we are safe to run these [these UPDATE and DELETE](https://github.com/gordonje/access_mo/blob/master/sql/dedupe_on_full_middle_name.sql) commands.

### Deduping Persons: Concatenate First and Middle Names

Next, we combine records like these:

	first_name | middle_name | last_name      | name_suffix 
	-----------+-------------+----------------+-------------
	J          | C           | Kuessner       |             
	JC         |             | Kuessner       |             

Where the person's first name is basically his first and middle initials. Put more abstractly, we're combining cases where the concatenation of the first name and middle name values are the same for each last name / name suffix combo. 

The success of this step relies on some of the normalization of these name field values (e.g., removing '.' and leading and trailing whitespace) that occurs when the person and person name records are added to the database (see [model_helpers.py](https://github.com/gordonje/access_mo/blob/master/model_helpers.py)).

So then we can just run these [these UPDATE and DELETE](https://github.com/gordonje/access_mo/blob/master/sql/dedupe_on_first_middle_concat.sql) commands.

### Deduping Persons: Concatenate Middle and Last Names

Next, we combine records like these:

	first_name | middle_name | last_name      | name_suffix 
	-----------+-------------+----------------+-------------
	Sharon     | Sanders     | Brooks         |             
	Sharon     |             | Sanders Brooks |             
	Robin      | Wright      | Jones          |             
	Robin      |             | Wright-Jones   |             

Which should be two person, not four. These are cases where the concatenation of the middle name and last name values are the same for each first name / name suffix combo. There might be a hyphen, whitespace or maybe some other character separating the middle and last names, but we can handle of these cases at once by running [these UPDATE and DELETE](https://github.com/gordonje/access_mo/blob/master/sql/dedupe_on_middle_last_concat.sql) commands.

### Deduping Persons: First Name Matches Nickname

Next, we need to combine records where the first name matches the nickname for a given last name / name suffix combo. For example, these records:

	first_name | last_name   | name_suffix | nickname 
	-----------+-------------+-------------+----------
	Anthony    | Leech       |             | Tony     
	Tony       | Leech       |             |          

Should become a single person.

First, we have to make sure nickname values are assigned to all of the person records that have related person name with a nickname value, which is one simple [UPDATE](https://github.com/gordonje/access_mo/blob/master/sql/fill_in_nicknames.sql) command. 

Then, run [these UPDATE and DELETE](https://github.com/gordonje/access_mo/blob/master/sql/dedupe_on_first_nickname.sql) commands.

### Deduping Persons: Formal Name Matches Diminutive First Name

Need, we need to combine records where the first name is the diminutive form of a formal name for a given last name / name suffix combo. For example, these 5 records:

	first_name | middle_name | last_name      | name_suffix 
	-----------+-------------+----------------+-------------
	Kenneth    |             | Jones          |             
	Kenny      |             | Jones          |             
	Ken        |             | Jones          |             
	Charlie    |             | Schlottach     |             
    Charles    | W           | Schlottach     |             

Should become 2 distinct persons.

For this step, we can pull in some outside help. This [repo](https://github.com/dtrebbien/diminutives.db) two .csv files of formal names and their diminutives, one for female formal names and one for male formal names. These files were downloaded and combined to a single tab-delimited file, then [loaded](https://github.com/gordonje/access_mo/blob/master/load_name_groups.py) into the name_groups table.

Then, we just need to run [these UPDATE and DELETE](https://github.com/gordonje/access_mo/blob/master/sql/dedupe_on_first_name_group.sql) commands.

### Deduping Persons: First Name Matches Middle Name

Finally, we're going to combine records where the last name and name suffix are the same and the first name matches the middle name. For example, these four records:

	first_name | middle_name | last_name      | name_suffix 
	-----------+-------------+----------------+-------------
	W          | Todd        | Akin           |             
	Todd       |             | Akin           |
	Gail       | McCann      | Beatty         |             
	E          | Gail        | Beatty         |             

Should become two person records. 

This second pair is a little suspect, but according to a [Missouri Times Q-and-A](http://themissouritimes.com/7215/five-questions-rep-gail-mccann-beatty-d-kansas-city/) from 2013, Gail McCann Beatty ran in the 1999 special election for the 43rd House District to which E Gail Beatty is assigned. So we are safe to run [these UPDATE and DELETE](https://github.com/gordonje/access_mo/blob/master/sql/dedupe_on_first_name_group.sql) commands.

### Deduping Persons: Wrap Up

Even after all that work, there are potentially still duplicate person records that can't be handled programmatically, such as when a person's last name changes completely (probably as a result of marriage or divorce). For example, after a research, we learned that these records:

	first_name | middle_name | last_name      | name_suffix 
	-----------+-------------+----------------+-------------
	Linda      |             | Black          |             
	Linda      | R           | Fishcer        |             

Actually represent [one person](http://house.mo.gov/member.aspx?year=2014&district=117), which has handled with a few ad-hoc commands. This and other manual dedupes are handled [here](https://github.com/gordonje/access_mo/blob/master/sql/manual_dedupes.sql).

Here's one set of records that might require further research:

	first_name | middle_name | last_name      | name_suffix 
	-----------+-------------+----------------+-------------
	John       | L           | Bowman         |             
	John       | L           | Bowman         | Jr          
	John       | L           | Bowman         | Sr          

There might be two John L Bowman, but there probably aren't three, and there's no clear path to map the related race_candidate records to the correct John L Bowman. We'll have to come back to this one.

It's also possible that we've erroneously combined some records, which is why we're reaching out the Missouri Legislative Research Library to confirm our results.

At the end of the day, we've taken 2,566 records and combined them into 2,367 distinct persons. 

Recall that our general and special election records reference the assembly to which each winning candidate was elected. So we can now use all this information to insert assembly member records, denoting which person represented which chamber and district in which assembly. We also have to insert additional assembly member records for senators, who are elected for four year terms (i.e., two general assemblies). These INSERT commands are in [insert_assembly_members.sql](https://github.com/gordonje/access_mo/blob/master/sql/insert_assembly_members.sql). Note that a few of the Senators elected via special election have to be handled separately on an ad-hoc basis.

Getting Session Data
--------------------

1.	Run get_past_sessions.py

2.	(Get session_member_profiles)
3.	(Get bill info)
4.	(Get bill actions)
5.	(Get bill co-sponsors)
6.	(Get bill summaries)
7.	(Get bill texts)


TODO
----

More generic model for sources and source docs
Modeling political parties