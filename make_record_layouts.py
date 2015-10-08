from models import *
from csv import DictWriter, DictReader

table_file_headers = None
out_tables = []
column_file_headers = [
	  'table_name'
	, 'column_name'
	, 'data_type'
	, 'character_maximum_length'
	, 'is_nullable'
	, 'ordinal_position'
	, 'description'
]

# Add table comments to db
with open('record_layouts/tables.tsv', 'rU', ) as f:

	reader = DictReader(f, delimiter='\t')
	table_file_headers = reader.fieldnames

	for row in reader:
		comment_q = "COMMENT ON TABLE {table} IS '{description}';".format(**row)
		db.execute_sql(comment_q)
		count_q = "SELECT * FROM {table};".format(**row)
		row['record_count'] = db.execute_sql(count_q).rowcount

		out_tables.append(row)

# Write record counts to tables.tsv file
with open('record_layouts/tables.tsv', 'w', ) as f:
	writer = DictWriter(f, delimiter='\t', fieldnames=table_file_headers)

	writer.writeheader()

	for table in out_tables:
		writer.writerow(table)

# Add column comments to db
for table in out_tables:
	
	model = globals()[table['table'].title()]

	for field in model._meta.get_sorted_fields():

		column = {
			  'table': table['table']
			, 'name': field[1].db_column
			, 'comment': field[1].help_text
		}

		if column['comment'] == None and column['name'] == 'id':
			column['comment'] = 'Primary key.'
		
		comment_q = "COMMENT ON COLUMN {table}.{name} IS '{comment}';".format(**column)

		db.execute_sql(comment_q)

# Write columns.tsv file:
with open('record_layouts/columns.tsv', 'w', ) as f:

	writer = DictWriter(
		  f
		, delimiter='\t'
		, fieldnames=column_file_headers
	)

	writer.writeheader()

	with open('sql/get_column_info.sql', 'rU') as f:
		col_q = f.read()

	for col in db.execute_sql(col_q).fetchall():
		writer.writerow(dict(zip(column_file_headers, col)))
