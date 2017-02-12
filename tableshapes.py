import math

def generate_oval(table):
	"""Generates the positions of the chairs around an oval table"""
	rx = table["width"] / 2
	ry = table["height"] / 2
	center_x = table["x_pos"] + rx
	center_y = table["y_pos"] + ry
	rx += 20
	ry += 20

	angle = 0
	increment = 2*math.pi / table["capacity"]

	# Generates points around an oval parametrically
	for i in range(table["capacity"]):
		yield (
			center_x + rx*math.cos(angle),
			center_y + ry*math.sin(angle)
		)
		angle += increment

def generate_two_side(table, capacity=None):
	"""Generates the positions of the chairs around a rectangular table
	with two sides full"""
	if capacity is None:
		capacity = table["capacity"]

	upper = table["x_pos"] + table["width"]

	# Generate top side
	n = capacity // 2
	y = table["y_pos"] - 20

	for x in generate_spaced(table["x_pos"], upper, n):
		yield (x, y)

	# Generate bottom side
	n = capacity - n
	y = table["y_pos"] + table["height"] + 20

	for x in generate_spaced(table["x_pos"], upper, n):
		yield (x, y)

def generate_four_side(table):
	"""Generates the positions of the chairs around a rectangular table
	with all four sides full"""
	upper = table["y_pos"] + table["height"]
	n = table["capacity"]*table["height"] / (table["width"]+table["height"])
	n = round(n) & ~1

	# Generate top and bottom
	# Any odd sides will always be passed to this function
	yield from generate_two_side(table, table["capacity"] - n)

	n //= 2

	# Generate left side
	x = table["x_pos"] - 20

	for y in generate_spaced(table["y_pos"], upper, n):
		yield (x, y)

	# Generate right side
	x = table["x_pos"] + table["width"] + 20

	for y in generate_spaced(table["y_pos"], upper, n):
		yield (x, y)

def generate_spaced(lower, upper, n):
	"""Generates positions in the center of equal width sections
	between lower and upper"""
	if n == 0: return

	spacing = (upper - lower) / n
	x = lower + spacing / 2

	for i in range(n):
		yield x
		x += spacing

def max_chairs(table):
	"""Calculates the maximum number of chairs that can fit
	around the given table"""
	if table["shape"] == 0:
		width = table["width"] + 40
		height = table["height"] + 40

		circumference = math.pi * math.sqrt((width*width + height*height) / 2)
		max_chairs = int(circumference // 37)
	else:
		max_chairs = (table["width"] + 5) // 37
		if table["shape"] == 2:
			max_chairs += (table["height"] + 5) // 37

		max_chairs *= 2

	return max_chairs

def get_shape(canvas, shape):
	if shape == 0:
		return canvas.create_oval(0, 0, 0, 0, width=2, fill="#EEE")
	else:
		return canvas.create_rectangle(0, 0, 0, 0, width=2, fill="#EEE")

SHAPES = (
	"Oval",
	"Rectangle (two sides)",
	"Rectangle (four sides)"
)
GENERATORS = (
	generate_oval,
	generate_two_side,
	generate_four_side
)

def generate_chairs(table):
	if table["capacity"] > 0:
		yield from GENERATORS[table["shape"]](table)
