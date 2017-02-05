import math

def validate_digits(after):
	return not after or after.isnumeric()

def table_number_in(tables, x):
	for table in tables:
		if table.table["table_number"].isnumeric() \
				and int(table.table["table_number"]) == x:
			return True
	return False

#def validate_positive(after):
#	try:
#		return not after or int(after) > 0
#	except ValueError: return False
