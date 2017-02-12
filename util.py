import data

def clamp(x, low, high):
	"""Limits x to the range [low, high]"""
	return low if x < low else high if x > high else x

def substr_match(a, b):
	"""Finds the highest n such that
	the first n characters of a and b are equal"""
	a = a.lower()
	b = b.lower()
	high = min(len(a), len(b))

	for i in range(high):
		if a[i] != b[i]: return i
	return high

def find_by_name(name):
	"""Finds the member that most closely matches the given name.

	For example, "sam" will more closely match "samuel" than "s".
	The comparison is case-insensitive"""
	max_match = 0
	max_id = None

	for id, member in data.members.items():
		# Can't be closest, a longer match has already been found
		if len(member["first_name"]) + len(member["last_name"]) + 1 < max_match:
			continue

		member_name = member["first_name"] + " " + member["last_name"]
		match = substr_match(name, member_name)

		if match > max_match:
			max_match = match
			max_id = id
	return max_id or -1

def unique_name(target):
	"""Finds the shortest substring of a target's name which 
	uniquely identifies them.

	This function will always include the person's complete first name"""
	name = target["first_name"]
	matches = list(filter(lambda member: member != target and member["first_name"] == name, data.members.values()))

	unique_length = 0
	if matches:
		for i in range(len(target["last_name"])):
			for match in matches:
				if match["last_name"][i] != target["last_name"][i]:
					matches.remove(match)

			if len(matches) == 0:
				unique_length = i + 1
				break

		if unique_length:
			name += " " + target["last_name"][:unique_length]
		else:
			name += " " + target["last_name"] + " " + str(target["member_id"])
	return name
