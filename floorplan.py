from tkinter import *
from tkinter.ttk import Separator
from constants import *
from util import validate_digits
import math

class TableDetails(LabelFrame):
	def __init__(self, master=None):
		LabelFrame.__init__(self, master, text="Table Details")

		self.fields = {}

		vcmd = (self.register(validate_digits), "%S")
		for i in range(len(TABLE_FIELDS)):
			field = TABLE_FIELDS[i]
			Label(self, text=field[1]).grid(row=i, sticky=E)
			self.fields[field[0]] = Entry(self)
			self.fields[field[0]].grid(row=i, column=1, sticky=EW)

			# Could also test for i != 0 for speed
			if field[0] != "table_number":
				self.fields[field[0]].configure(vcmd=vcmd, validate="key")

		self.vars = {field: StringVar() for field in self.fields}
		for key in self.vars:
			self.vars[key].trace("w", lambda a, b, c: self.edited())
			self.fields[key]["textvariable"] = self.vars[key]

	def edited(self):
		if self.loading: return

		x = self.fields["x_pos"].get()
		x = int(x) if x.isnumeric() else 0
		y = self.fields["y_pos"].get()
		y = int(y) if y.isnumeric() else 0

		width = self.fields["width"].get()
		width = int(width) if width.isnumeric() else 0
		height = self.fields["height"].get()
		height = int(height) if height.isnumeric() else 0

		capacity = self.fields["capacity"].get()
		capacity = int(capacity) if capacity.isnumeric() else 0

		# Don't have to validate integer
		self.table.table["table_number"] = self.fields["table_number"].get()

		self.table.move(x, y, False)
		self.table.set_chairs(capacity)
		self.table.resize(width, height)

	def load_table(self, table=None):
		self.table = table
		self.loading = True

		if table:
			for field in self.fields:
				self.fields[field].delete(0, END)
				self.fields[field].insert(0, table.table[field])

		self.loading = False

class Table:
	def __init__(self, table, canvas, selectcallback):
		self.table = table
		self.canvas = canvas
		self.selectcallback = selectcallback

		self.chairs = []
		self.set_shape(0)
		self.table_number = self.canvas.create_text(0, 0)

		self.move(table["x_pos"], table["y_pos"], False)
		self.resize(table["width"], table["height"], False)
		self.set_chairs(3)
		self.update_position()

	def mouse_down(self, e):
		self.offset = (e.x - self.table["x_pos"], e.y - self.table["y_pos"])
		self.selectcallback(self)

	def mouse_move(self, e):
		x = e.x_root - self.offset[0] - self.canvas.winfo_rootx()
		y = e.y_root - self.offset[1] - self.canvas.winfo_rooty()
		self.move(x, y)

	def move(self, x, y, update=True):
		self.table["x_pos"] = x
		self.table["y_pos"] = y
		if update:
			self.update_position()

	def resize(self, width, height, update=True):
		self.table["width"] = width
		self.table["height"] = height
		if update:
			self.update_position()

	def set_bounds(self, left, top, right, bottom, update):
		self.move(left, top, False)
		self.resize(right-left, bottom-top, update)

	def set_shape(self, shape):
		self.shape = self.canvas.create_oval(0, 0, 0, 0, width=2, fill="#eeeeee")
		self.canvas.tag_bind(self.shape, "<Button-1>", self.mouse_down)
		self.canvas.tag_bind(self.shape, "<B1-Motion>", self.mouse_move)

	def set_chairs(self, count=None):
		if not count is None:
			self.table["capacity"] = count

		# Add new chairs if we don't have enough
		if self.table["capacity"] > len(self.chairs):
			for i in range(len(self.chairs), self.table["capacity"]):
				self.chairs.append(self.canvas.create_oval(0, 0, 32, 32, fill="#dddddd"))
		else: # Remove any extra
			while len(self.chairs) > self.table["capacity"]:
				self.canvas.delete(self.chairs.pop())

		if self.table["capacity"] == 0: return

		rx = self.table["width"] / 2
		ry = self.table["height"] / 2
		center_x = self.table["x_pos"] + rx
		center_y = self.table["y_pos"] + ry
		rx += 20
		ry += 20

		angle = 0
		increment = 2*math.pi / self.table["capacity"]
		for i in range(self.table["capacity"]):
			x = center_x + rx*math.cos(angle)
			y = center_y + ry*math.sin(angle)
			angle += increment

			self.canvas.coords(self.chairs[i], x - 16, y - 16, x + 16, y + 16)

	def update_position(self):
		self.canvas.coords(self.shape, self.table["x_pos"], self.table["y_pos"], self.table["x_pos"] + self.table["width"], self.table["y_pos"] + self.table["height"])
		self.set_chairs()

		self.canvas.dchars(self.table_number, 0, END)
		self.canvas.insert(self.table_number, 0, "Table {}\nEmpty".format(self.table["table_number"]))
		self.canvas.coords(self.table_number, self.table["x_pos"] + self.table["width"] / 2, self.table["y_pos"] + self.table["height"] / 2)

		self.selectcallback(self)

class FloorPlan(Frame):
	def __init__(self, master=None):
		Frame.__init__(self, master)

		top = Frame(self, relief=SUNKEN, border=1)
		top.grid(row=0, column=0, sticky=EW, columnspan=2)

		top.columnconfigure(0, minsize=2)
		top.rowconfigure(0, minsize=2)
		top.rowconfigure(2, minsize=2)

		self.edit = Button(top, text="Edit", command=self.toggle_editing)
		self.edit.grid(row=1, column=1)
		Separator(top, orient=VERTICAL).grid(row=1, column=2, sticky=NS, padx=10)

		self.new_table = Button(top, text="New Table", command=self.add_table)
		self.new_table.grid(row=1, column=3)
		self.delete_table = Button(top, text="Delete Table")
		self.delete_table.grid(row=1, column=4, padx=5)

		self.floor_view = Canvas(self, border=1, relief=RAISED, bg="white")
		self.floor_view.grid(row=2, column=0, sticky=NSEW)

		self.details = TableDetails(self)
		self.details.grid(row=2, column=1, sticky=NSEW, padx=5, pady=5)

		self.columnconfigure(0, weight=1)
		self.rowconfigure(1, minsize=5)
		self.rowconfigure(2, weight=1)

		self.tables = []
		self.set_editing(False)

	def select_table(self, table):
		self.selected = table
		self.details.load_table(table)

	def add_table(self):
		table = { # This should be put somewhere else, or removed
			"x_pos": 5,
			"y_pos": 5,
			"width": 100,
			"height": 100,
			"capacity": 4,
			"table_number": "",
			"shape": 0
		}
		self.tables.append(Table(table, self.floor_view, self.select_table))

	def toggle_editing(self):
		self.set_editing(not self.editing)

	def set_editing(self, editing):
		self.editing = editing
		self.edit["text"] = "Finish" if self.editing else "Edit"

		if self.editing:
			self.new_table.grid()
			self.delete_table.grid()
			self.details.grid()
		else:
			self.new_table.grid_remove()
			self.delete_table.grid_remove()
			self.details.grid_remove()
