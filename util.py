def validate_digits(after):
	return not after or after.isnumeric()

#def validate_positive(after):
#	try:
#		return not after or int(after) > 0
#	except ValueError: return False
