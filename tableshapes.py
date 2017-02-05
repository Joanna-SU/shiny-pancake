import math

OVAL      = 0
TWO_SIDE  = 1
FOUR_SIDE = 2

SHAPES = [
	"Oval",
	"Rectangle (two sides)",
	"Rectangle (four sides)"
]

def generate_oval(table):
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
	if n == 0: return

	spacing = (upper - lower) / n
	x = lower + spacing / 2

	for i in range(n):
		yield x
		x += spacing

generators = [
	generate_oval,
	generate_two_side,
	generate_four_side
]

def generate_chairs(table):
	if table["capacity"] > 0:
		yield from generators[table["shape"]](table)
