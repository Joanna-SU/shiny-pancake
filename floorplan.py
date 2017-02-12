import tableshapes, data, util, tkinter, tkinter.ttk, sqlite3, datetime, math
from constants import *

DEFAULT_TABLE = {
	"x_pos": 41, "y_pos": 41, # Allows padding for chairs and a 5px margin
	"width": 100, "height": 100,
	"capacity": 4,
	"table_number": "",
	"shape": 0 # Oval
}

class TableDetails(tkinter.LabelFrame):
	def __init__(self, master=None):
		tkinter.LabelFrame.__init__(self, master, text="Table Details")

		self.fields = {}
		vcmd = (self.register(lambda text: not text or text.isnumeric()), "%S")

		row = 0
		for key, name in TABLE_FIELDS:
			tkinter.Label(self, text=name).grid(row=row, sticky=E)
			self.fields[key] = tkinter.Entry(self)
			self.fields[key].grid(row=row, column=1, sticky=EW)

			if key != "table_number":
				self.fields[key].configure(vcmd=vcmd, validate="key")
			row += 1

		# Tracks the string shape of the table
		self.shape = tkinter.StringVar()
		self.shape.trace("w", self.edited)

		tkinter.Label(self, text="Shape").grid(row=len(TABLE_FIELDS), sticky=E)
		self.shape_menu = tkinter.OptionMenu(self, self.shape, *tableshapes.SHAPES)
		self.shape_menu.grid(row=len(TABLE_FIELDS), column=1, sticky=EW)

		self.vars = {field: tkinter.StringVar() for field in self.fields}
		for key in self.vars:
			self.vars[key].trace("w", self.edited)
			self.fields[key]["textvariable"] = self.vars[key]

		self.load_table(None)

	def edited(self, *args, **kwargs):
		"""Handles and validates modifications to any table"""
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

		# Don't have to validate integer (can be e.g. 5b)
		self.table.table["table_number"] = self.fields["table_number"].get()

		self.table.move(x, y, False)
		self.table.set_shape(tableshapes.SHAPES.index(self.shape.get()))
		self.table.set_chairs(capacity)
		self.table.resize(width, height)

	def load_table(self, table=None):
		"""Loads the details from the given table into this form"""
		self.table = table
		self.loading = True

		state = NORMAL if table else DISABLED

		for field in self.fields:
			self.fields[field].delete(0, END)
			self.fields[field]["state"] = state
		self.shape_menu["state"] = state

		if table:
			for field in self.fields:
				self.fields[field].insert(0, table.table[field])

			self.shape.set(tableshapes.SHAPES[table.table["shape"]])
		else:
			self.shape.set("")

		self.loading = False

class Table:
	def __init__(self, table, canvas, selectcallback, menucallback):
		self.table = table
		self.canvas = canvas
		self.selectcallback = selectcallback
		self.menucallback = menucallback

		self.editing = False
		self.chairs = []
		self.shape = None
		self.table_number = self.canvas.create_text(0, 0)

		self.current_booking = None
		self.status_since = -1 # Time since the status was last changed
		self.waiter = None
		self.waiter_text = 0
		self.waiter_box = 0

		# Set up the position of the table
		self.move(table["x_pos"], table["y_pos"], False)
		self.resize(table["width"], table["height"], False)
		self.set_chairs(table["capacity"])
		self.set_shape(table["shape"])

		self.update_position()
		self.ping = False

	def set_status(self, status):
		"""Updates the database with the given status and calculates
		a new estimated next status time"""
		if self.current_booking:
			data.cursor.execute(data.SET_STATUS, (status, self.current_booking["booking_id"]))
			data.database.commit()
			self.current_booking["status"] = status
			self.status_since = datetime.datetime.now().timestamp()

			self.update_text()

	def set_waiter(self, waiter=None):
		"""Assigns the given waiter to this table, displaying their name"""
		if self.waiter: # Take load off of current waiter, if any
			data.current_work[self.waiter["member_id"]] -= 1

		if waiter:
			self.waiter = waiter
			# Add load to new waiter
			data.current_work[waiter["member_id"]] += 1
			name = util.unique_name(self.waiter)

			if self.waiter_text: # Might never be true
				self.canvas.dchars(self.waiter_text, 0, END)
				self.canvas.insert(self.waiter_text, 0, name)

				self.canvas.coords(self.waiter_text, self.table["x_pos"] + 5, self.table["y_pos"] + 5)

				bounds = self.canvas.bbox(self.waiter_text)
				bounds = (bounds[0] - 5, bounds[1] - 5, bounds[2] + 5, bounds[3] + 5)

				self.canvas.coords(self.waiter_box, bounds)
			else:
				self.waiter_text = self.canvas.create_text(
					self.table["x_pos"] + 5, self.table["y_pos"] + 5,
					text=name, anchor=W, fill="white")

				bounds = self.canvas.bbox(self.waiter_text)
				bounds = (bounds[0] - 5, bounds[1] - 5, bounds[2] + 5, bounds[3] + 5)

				self.waiter_box = self.canvas.create_rectangle(bounds, fill="red", outline="white", width="1")
				self.canvas.tag_lower(self.waiter_box, self.waiter_text)
		else:
			self.canvas.delete(self.waiter_text)
			self.canvas.delete(self.waiter_box)
			self.waiter_text = 0

	def mouse_down(self, e):
		if self.editing:
			self.offset = (e.x - self.table["x_pos"], e.y - self.table["y_pos"])
			self.selectcallback(self)

	def right_down(self, e):
		if not self.editing:
			self.menucallback(self, e.x_root, e.y_root)

	def mouse_move(self, e):
		if self.editing:
			x = e.x_root - self.offset[0] - self.canvas.winfo_rootx()
			y = e.y_root - self.offset[1] - self.canvas.winfo_rooty()
			self.move(x, y)

	def move(self, x, y, update=True):
		self.table["x_pos"] = x
		self.table["y_pos"] = y
		if update:
			self.update_position()

	def resize(self, width, height, update=True):
		self.table["width"] = min(width, 1000)
		self.table["height"] = min(height, 1000)
		if update:
			self.update_position()

	def set_bounds(self, left, top, right, bottom, update):
		self.move(left, top, False)
		self.resize(right-left, bottom-top, update)

	def set_shape(self, shape):
		"""Sets the visible shape of table"""
		self.table["shape"] = shape
		if not self.shape is None:
			self.canvas.delete(self.shape)

		self.shape = tableshapes.get_shape(self.canvas, shape)
		self.canvas.tag_bind(self.shape, "<Button-1>", self.mouse_down)
		self.canvas.tag_bind(self.shape, "<B1-Motion>", self.mouse_move)
		self.canvas.tag_bind(self.shape, "<Button-3>", self.right_down)
		self.canvas.lower(self.shape, self.table_number) # Move to back

	# Brings the amount of chairs on a table to a number that fits
	def limit_chairs(self):
		"""Lowers the amount of chairs at the table, if necessary,
		so that they all fit around the shape"""
		max_chairs = tableshapes.max_chairs(self.table)
		if self.table["capacity"] > max_chairs:
			self.table["capacity"] = max_chairs

	def set_chairs(self, count=None):
		"""Redraws the chairs around the table, as well as
		calculating their positions"""
		if not count is None:
			self.table["capacity"] = count
		self.limit_chairs()

		# Add new chairs if we don't have enough
		if self.table["capacity"] > len(self.chairs):
			for i in range(len(self.chairs), self.table["capacity"]):
				self.chairs.append(self.canvas.create_oval(0, 0, 32, 32, fill="#DDD"))
		else: # Remove any extra
			while len(self.chairs) > self.table["capacity"]:
				self.canvas.delete(self.chairs.pop())

		i = 0
		for point in tableshapes.generate_chairs(self.table):
			self.canvas.coords(self.chairs[i],
				point[0] - 16, point[1] - 16, point[0] + 16, point[1] + 16)
			i += 1

		self.canvas.lift(self.waiter_box)
		self.canvas.lift(self.waiter_text)

	def update_text(self):
		"""Rewrites the text in the center of the table
		based on the booking and the current mode"""
		lines = ["Table " + self.table["table_number"]]

		if not self.editing and self.current_booking:
			# The customers at this table have left
			if self.current_booking["status"] == COMPLETED:
				self.current_booking = None
				self.set_waiter(None)
				self.canvas.itemconfig(self.shape, fill="#EEE")
				self.ping = False
			else:
				lines.append(STATUSES[self.current_booking["status"]])

				# Adds time information
				if self.current_booking["status"] == EMPTY:
					lines.append(datetime.datetime.fromtimestamp(self.current_booking["arrival"]).strftime("%H:%M"))
				else:
					next_time = self.status_since + STATUS_TIMES[self.current_booking["status"]]
					lines.append("{}-{}".format(
						datetime.datetime.fromtimestamp(self.status_since).strftime("%H:%M"),
						datetime.datetime.fromtimestamp(next_time).strftime("%H:%M")
					))
				self.canvas.itemconfig(self.shape, fill=TABLE_COLORS[self.current_booking["status"]])

		self.canvas.coords(self.table_number, self.table["x_pos"] + self.table["width"] / 2, self.table["y_pos"] + self.table["height"] / 2)

		self.canvas.dchars(self.table_number, 0, END)
		self.canvas.insert(self.table_number, 0, '\n'.join(lines))

	def update_position(self):
		"""Visibly moves the shapes on the canvas when the table is moved"""
		self.canvas.coords(self.shape, self.table["x_pos"], self.table["y_pos"],
			self.table["x_pos"] + self.table["width"], self.table["y_pos"] + self.table["height"])

		self.set_chairs()
		self.update_text()
		self.set_waiter(self.waiter)
		self.selectcallback(self)

	def set_editing(self, editing):
		self.editing = editing
		self.update_text()

	def toggle_ping(self):
		self.ping = not self.ping

	def set_flash(self, flash):
		"""Sets the animation state of the table's ping"""
		self.canvas.itemconfig(self.shape,
			outline="red" if self.ping and flash else "black",
			width=4 if self.ping else 2)

	def cleanup(self):
		"""Deletes all the shapes this table used on the canvas"""
		self.canvas.delete(self.shape)
		self.canvas.delete(self.table_number)
		self.canvas.delete(self.waiter_text)

		for chair in self.chairs:
			self.canvas.delete(chair)

class FloorPlan(tkinter.Frame):
	def __init__(self, callback, master=None):
		tkinter.Frame.__init__(self, master)
		self.callback = callback

		self.init_toolbar()
		self.floor_view = tkinter.Canvas(self, border=1, relief=RAISED, bg="white")
		self.floor_view.grid(row=2, column=0, sticky=NSEW)
		self.details = TableDetails(self)
		self.details.grid(row=2, column=1, sticky=NSEW, padx=5, pady=5)

		self.columnconfigure(0, weight=1)
		self.rowconfigure(1, minsize=5)
		self.rowconfigure(2, weight=1)

		self.tables = []
		self.populate()
		self.set_editing(False)
		self.check_bookings(True)
		self.flash = False
		self.animate_pings()
		self.init_menu()

	def init_toolbar(self):
		"""Initializes the mode toggle, and table management buttons"""
		top = tkinter.Frame(self, relief=SUNKEN, border=1)
		top.grid(row=0, column=0, sticky=EW, columnspan=2)

		top.columnconfigure(0, minsize=2)
		top.rowconfigure(0, minsize=2)
		top.rowconfigure(2, minsize=2)

		self.edit = tkinter.Button(top, text="Edit", command=self.toggle_editing)
		self.edit.grid(row=1, column=1)
		tkinter.ttk.Separator(top, orient=VERTICAL).grid(row=1, column=2, sticky=NS, padx=10)

		self.new_table = tkinter.Button(top, text="New Table", command=self.add_table)
		self.new_table.grid(row=1, column=3)
		self.delete_table = tkinter.Button(top, text="Delete Table", command=self.delete_table)
		self.delete_table.grid(row=1, column=4, padx=5)
		self.find_button = tkinter.Button(top, text="Find Lost Tables", command=self.find_lost)
		self.find_button.grid(row=1, column=5)

	def find_lost(self):
		"""Finds and moves lost tables into the visible screen region"""
		max_x = self.floor_view.winfo_width() - 41
		max_y = self.floor_view.winfo_height() - 41

		for table in self.tables:
			table.move(util.clamp(table.table["x_pos"], 41, max_x - table.table["width"]),
				util.clamp(table.table["y_pos"], 41, max_y - table.table["height"]))

	def show_menu(self, table, x, y):
		"""Shows the table right-click menu"""
		self.select_table(table)
		if not self.editing and self.selected.current_booking:
			self.menu.post(x, y)

	def select_table(self, table):
		self.selected = table
		self.details.load_table(table)

	def populate(self):
		"""Adds all the tables from the database to the floor view"""
		now = datetime.datetime.now().timestamp()
		for table in data.tables.values():
			floor_table = Table(table, self.floor_view, self.select_table, self.show_menu)
			floor_table.status_since = now
			self.tables.append(floor_table)

	def add_table(self):
		"""Adds a new default table to both the database and to the floor plan.

		This function does not commit the database"""
		new_table = dict(DEFAULT_TABLE)

		# Finds the lowest available table number
		lowest = 1
		found = False
		while not found:
			found = True # Assume the next number is available

			for table in self.tables:
				if table.table["table_number"].isnumeric() \
						and int(table.table["table_number"]) == lowest:
					found = False # Keep looking
					lowest += 1
					break
			# This loop will break once a number is found

		new_table["table_number"] = str(lowest)

		# Upload the table
		data.cursor.execute(data.ADD_TABLE, (
			new_table["table_number"],
			new_table["capacity"],
			new_table["x_pos"], new_table["y_pos"],
			new_table["width"], new_table["height"],
			new_table["shape"]
		))
		new_table["table_id"] = data.cursor.lastrowid
		data.tables[new_table["table_id"]] = new_table # Add to the local cache

		# Convert to a canvas table
		canvas_table = Table(new_table, self.floor_view, self.select_table, self.show_menu)
		canvas_table.set_editing(True)
		self.tables.append(canvas_table)

	def delete_table(self):
		"""Removes the selected table from both the database and the floor plan.

		This function does not commit the database"""
		if self.selected:
			self.selected.cleanup()
			id = self.selected.table["table_id"]

			# Delete from the db
			data.cursor.execute(data.DELETE_TABLE, (id, ))

			del data.tables[id] # Remove from the local cache
			self.tables.remove(self.selected)
			self.select_table(None)

	def commit(self):
		"""Uploads changes to properties and commits to the db"""
		for table in data.tables.values():
			# Tables don't keep track of if they have been changed,
			# so all are updated
			data.cursor.execute(data.MODIFY_TABLE, (
				table["table_number"],
				table["capacity"],
				table["x_pos"], table["y_pos"],
				table["width"], table["height"],
				table["shape"],
				table["table_id"]
			))

		data.database.commit()

	def toggle_editing(self):
		self.set_editing(not self.editing)

	def set_editing(self, editing):
		"""Switches between edit mode and running mode"""
		self.editing = editing
		self.edit["text"] = "Finish" if self.editing else "Edit"

		for table in self.tables:
			table.set_editing(editing)

		if self.editing:
			self.new_table.grid()
			self.delete_table.grid()
			self.find_button.grid()
			self.details.grid()
		else:
			self.new_table.grid_remove()
			self.delete_table.grid_remove()
			self.find_button.grid_remove()
			self.details.grid_remove()

			self.commit()
			self.callback()

	def change_status(self, status=None):
		"""Either increments or sets the booking status of the selected table"""
		if not self.selected or not self.selected.current_booking: return

		if status is None:
			status = self.selected.current_booking["status"] + 1
		self.selected.set_status(status)

	def toggle_ping(self):
		"""Toggles ping on the selected table"""
		if not self.selected or not self.selected.current_booking: return
		self.selected.toggle_ping()

	def init_menu(self):
		"""Initializes the right-click table menu"""
		self.menu = tkinter.Menu(self, tearoff=False)
		status = tkinter.Menu(self.menu, tearoff=False)

		for i in range(len(STATUSES)):
			status.add_command(label=STATUSES[i], command=lambda i=i: self.change_status(i))

		self.menu.add_cascade(label="Change status...", menu=status)
		self.menu.add_command(label="Next status", command=self.change_status)
		self.menu.add_command(label="Toggle ping", command=self.toggle_ping)

	def check_bookings(self, allow_started=False):
		"""Starts a periodic cycle of checking for bookings that are
		coming up soon, and displaying them on their tables"""
		threshold = datetime.datetime.now().timestamp() + 1200 # 10 minutes in the future
		soon = list(filter(lambda b: b["arrival"] < threshold, data.bookings.values()))

		for table in self.tables:
			for booking in soon:
				if booking["table_id"] == table.table["table_id"] \
						and table.current_booking != booking \
						and booking["status"] != COMPLETED:
					# A new booking is starting soon at this table
					if table.current_booking and not allow_started:
						args = (
							table.table["table_number"],
							datetime.datetime.fromtimestamp(table.current_booking["arrival"]).strftime("%H:%M")
						)
						tkinter.messagebox.showerror("Booking Clash", "There is a booking at table {} for {}, but this table is still occupied.".format(*args))
					else:
						table.current_booking = booking
						table.update_text()

						# Don't allocate someone who isn't here
						possible = list(filter(lambda k: data.members[k]["present"], data.current_work.keys()))
						if possible:
							waiter = data.members[min(possible, key=data.current_work.get)]
							table.set_waiter(waiter)
					soon.remove(booking)
					break
		# Set a delay before calling this again
		self.after(10000, self.check_bookings)

	def animate_pings(self):
		"""Periodically tells all the tables with pings to flash"""
		self.flash = not self.flash

		for table in self.tables:
			table.set_flash(self.flash)
		self.after(500, self.animate_pings)
