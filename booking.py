import data, tkinter, tkinter.messagebox, datetime
from constants import *

class BookingForm(tkinter.LabelFrame):
	def __init__(self, master=None, text=None):
		tkinter.LabelFrame.__init__(self, master, text=text)

		self.columnconfigure(1, weight=1)
		self.columnconfigure(2, weight=2, minsize=100)

		tkinter.Label(self, text="Name").grid(sticky=E)
		self.customer = tkinter.Entry(self)
		self.customer.grid(row=0, column=1, sticky=EW)

		tkinter.Label(self, text="Table").grid(row=1, sticky=E)
		self.table = tkinter.StringVar(self)
		self.table_menu = tkinter.OptionMenu(self, self.table, ())
		self.table_menu.grid(row=1, column=1, sticky=EW)

		tkinter.Label(self, text="Time").grid(row=2, sticky=E)
		self.arrival = tkinter.Entry(self)
		self.arrival.grid(row=2, column=1, sticky=EW)
		tkinter.Label(self, text="YYYY-MM-DD HH:MM").grid(row=3, column=1, sticky=W)

	def populate_tables(self):
		"""Populates the menu of the table picker"""
		self.table_menu["menu"].delete(0, END)

		for id, table in data.tables.items():
			table_number = table["table_number"]

			self.table_menu["menu"].add_command(label=table_number,
				command=lambda n=table_number: self.table.set(n))

	def clear_fields(self):
		self.customer.delete(0, END)
		self.table.set("")
		self.arrival.delete(0, END)

	def load_booking(self, booking):
		self.customer.insert(0, booking["customer"])
		self.table.set(data.tables[booking["table_id"]]["table_number"])
		self.arrival.insert(0, datetime.datetime.fromtimestamp(booking["arrival"]).strftime(TIME_FORMAT))

	def get_table_id(self):
		"""Converts the string in the table selector to an ID"""
		table_id = -1
		for table in data.tables:
			if data.tables[table]["table_number"] == self.table.get():
				table_id = table
				break

		if table_id == -1:
			tkinter.messagebox.showerror("Invalid details", "You must specify a table.")
		return table_id

	def get_arrival(self):
		"""Converts the string in the date input box to a timestamp"""
		try:
			arrival = datetime.datetime.strptime(self.arrival.get(), TIME_FORMAT)
			if arrival <= datetime.datetime.now(): raise ValueError()
		except ValueError:
			tkinter.messagebox.showerror("Invalid details", "You must provide a valid future date and time, in the format YYYY-MM-DD HH:MM.")
			return -1

		# A booking in the morning is likely to be a mistake
		if arrival.hour < 12:
			if not tkinter.messagebox.askyesno("Are you sure?", "You have specified a time in the morning. Are you sure this is correct?"):
				return -1

		return arrival.timestamp()

class AddBooking(BookingForm):
	def __init__(self, addcallback, master=None):
		BookingForm.__init__(self, master, "Add a Booking")
		self.fill_time()
		self.addcallback = addcallback

		self.submit = tkinter.Button(self, text="Add", command=self.add)
		self.submit.grid(row=3, columnspan=2, pady=5, sticky=E)

		tkinter.Button(self, text="Now", command=self.fill_time).grid(row=2, column=2, sticky=W, padx=5)

	def fill_time(self):
		"""Fills the time input with the current date and time"""
		self.arrival.delete(0, END)
		self.arrival.insert(0, datetime.datetime.now().strftime(TIME_FORMAT))

	def add(self):
		"""Processes submitting the form"""
		booking = {
			"customer": self.customer.get(),
			"table_id": self.get_table_id(),
			"arrival": self.get_arrival()
		}
		if booking["table_id"] == -1 or booking["arrival"] == -1: return

		self.addcallback(booking)
		self.clear_fields()
		self.fill_time()

class EditBooking(BookingForm):
	def __init__(self, modifycallback, deletecallback, master=None):
		BookingForm.__init__(self, master, "Edit Booking")

		arrival_var = tkinter.StringVar(self)
		arrival_var.trace("w", lambda a, b, c: self.set_modified())
		self.arrival["textvariable"] = arrival_var
		self.table.trace("w", lambda a, b, c: self.set_modified())

		customer_var = tkinter.StringVar(self)
		customer_var.trace("w", lambda a, b, c: self.set_modified())
		self.customer["textvariable"] = customer_var

		self.modifycallback = modifycallback
		self.deletecallback = deletecallback

		buttons = tkinter.Frame(self)
		buttons.grid(row=3, columnspan=2, sticky=NSEW)

		self.modify = tkinter.Button(buttons, text="Modify", command=self.modify)
		self.modify.pack(side=RIGHT, pady=5)
		self.delete = tkinter.Button(buttons, text="Delete", command=self.delete)
		self.delete.pack(side=RIGHT, padx=5, pady=5)

		self.booking = None

	def set_modified(self, modified=True):
		self.modified = modified
		self.modify["state"] = NORMAL if self.modified else DISABLED

	def modify(self):
		"""Processes modifying a booking (clicking the modify button)"""
		table_id = self.get_table_id()
		if table_id == -1: return

		arrival = self.get_arrival()
		if arrival == -1: return

		self.booking["customer"] = self.customer.get()
		self.booking["table_id"] = table_id
		self.booking["arrival"] = arrival

		self.modifycallback(self.booking)
		self.set_modified(False)

	def delete(self):
		self.deletecallback(self.booking)
		self.load(None)

	def load(self, booking):
		"""Displays the information of a booking when selected"""
		if self.booking and self.modified:
			if not messagebox.askyesno("Are you sure?",
					"You have made changes to this booking.\nAre you sure you want to " \
					"discard these changes?"):
				return False
		self.clear_fields()
		if booking: self.load_booking(booking)

		self.booking = booking
		self.set_modified(False)

		return True

class BookingManager(tkinter.Frame):
	def __init__(self, master=None):
		tkinter.Frame.__init__(self, master)

		panes = tkinter.PanedWindow(self, sashwidth=5, sashrelief=RAISED, sashpad=5)
		panes.grid(padx=5, pady=5, sticky=NSEW)

		self.bookings = tkinter.Listbox(panes)
		self.booking_ids = []

		self.populate_list()
		self.bookings.bind("<<ListboxSelect>>", self.select)
		panes.add(self.bookings)

		self.init_forms(panes)

		self.rowconfigure(0, weight=1)
		self.columnconfigure(0, weight=1)
		self.select()

	def populate_tables(self):
		self.add_booking.populate_tables()
		self.edit_booking.populate_tables()

	def populate_list(self):
		"""Grabs bookings from the database cache and adds them to the list"""
		self.bookings.delete(0, END)
		self.booking_ids.clear()

		for booking in data.bookings.values():
			self.bookings.insert(END, booking["customer"])
			self.booking_ids.append(booking["booking_id"])

	# Callbacks for different forms

	def booking_added(self, booking):
		"""Adds a new booking to the database"""
		if booking:
			data.cursor.execute(data.ADD_BOOKING, (booking["customer"], booking["table_id"], booking["arrival"]))
			data.database.commit()

			booking["booking_id"] = data.cursor.lastrowid
			booking["status"] = EMPTY
			data.bookings[booking["booking_id"]] = booking

			self.populate_list()

	def booking_modified(self, booking):
		"""Updates the given booking with the new information"""
		if booking:
			data.cursor.execute(data.MODIFY_BOOKING, (booking["customer"], booking["table_id"], booking["arrival"], booking["booking_id"]))

			data.database.commit()
			self.populate_list()

	def booking_deleted(self, booking):
		"""Removes a booking from the database"""
		if booking:
			data.cursor.execute(data.DELETE_BOOKING, (booking["booking_id"], ))
			data.database.commit()

			del data.bookings[booking["booking_id"]]
			self.populate_list()
			self.select(None)

	# End callbacks

	def init_forms(self, panes):
		"""Initializes the add and edit booking forms"""
		forms = tkinter.Frame(panes)
		forms.columnconfigure(0, weight=1)

		self.add_booking  = AddBooking(self.booking_added, forms)
		self.edit_booking = EditBooking(self.booking_modified, self.booking_deleted, forms)

		self.add_booking.grid(row=1, sticky=EW)
		self.edit_booking.grid(row=2, sticky=EW)

		panes.add(forms)

	def select(self, event=None):
		"""Shows and hides the edit booking form when necessary"""
		booking = self.bookings.curselection()
		if booking:
			self.edit_booking.grid()

			booking = data.bookings[self.booking_ids[booking[0]]]
			self.edit_booking.load(booking)
		else:
			self.edit_booking.grid_remove()
