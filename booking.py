from tkinter import *
from tkinter import messagebox
from data import *
from constants import *
import os, sqlite3
from datetime import datetime

class BookingForm(LabelFrame):
	def __init__(self, master=None, text=None):
		LabelFrame.__init__(self, master, text=text)

		self.columnconfigure(1, weight=1)
		self.columnconfigure(2, weight=2, minsize=100)

		Label(self, text="Table").grid(row=1, sticky=E)
		self.table = StringVar(self)
		self.table_menu = OptionMenu(self, self.table, ())
		self.table_menu.grid(row=1, column=1, sticky=EW)
		self.table_ids = []

		Label(self, text="Time").grid(row=2, sticky=E)
		self.arrival = Entry(self)
		self.arrival.grid(row=2, column=1, sticky=EW)
		Label(self, text="YYYY-MM-DD HH:MM").grid(row=2, column=2, sticky=W)

	# Populates the menu of the table picker
	def populate_tables(self):
		self.table_ids.clear()
		self.table_menu["menu"].delete(0, END)

		for table in tables:
			self.table_ids.append(table)
			self.table_menu["menu"].add_command(
				label=tables[table]["table_number"],
				command=lambda table=table: self.table.set(tables[table]["table_number"])
			)

	def clear_fields(self):
		self.table.set("")
		self.arrival.delete(0, END)

	def load_booking(self, booking):
		self.table.set(tables[booking["table_id"]]["table_number"])
		self.arrival.insert(0, datetime.fromtimestamp(booking["arrival"]).strftime(TIME_FORMAT))

	def get_table_id(self):
		table_id = -1
		for table in tables:
			if tables[table]["table_number"] == self.table.get():
				table_id = table
				break

		if table_id == -1:
			messagebox.showerror("Invalid details", "You must specify a table.")
		return table_id

	def get_arrival(self):
		try:
			arrival = datetime.strptime(self.arrival.get(), TIME_FORMAT)
			if arrival <= datetime.now(): raise ValueError()
		except ValueError:
			messagebox.showerror("Invalid details", "You must provide a valid future date and time, in the format YYYY-MM-DD HH:MM.")
			return -1

		# A booking in the morning is likely to be a mistake
		if arrival.hour < 12:
			if not messagebox.askyesno("Are you sure?", "You have specified a time in the morning. Are you sure this is correct?"):
				return -1

		return arrival.timestamp()

class AddBooking(BookingForm):
	def __init__(self, addcallback, master=None):
		BookingForm.__init__(self, master, "Add a Booking")
		self.addcallback = addcallback

		self.submit = Button(self, text="Add", command=self.add)
		self.submit.grid(row=3, columnspan=2, pady=5, sticky=E)

	def add(self):
		booking = {
			"table_id": self.get_table_id(),
			"arrival": self.get_arrival()
		}
		if booking["table_id"] == -1 or booking["arrival"] == -1: return

		self.addcallback(booking)
		self.clear_fields()

class EditBooking(BookingForm):
	def __init__(self, modifycallback, deletecallback, master=None):
		BookingForm.__init__(self, master, "Edit Booking")

		arrival_var = StringVar(self)
		arrival_var.trace("w", lambda a, b, c: self.set_modified())
		self.arrival["textvariable"] = arrival_var
		self.table.trace("w", lambda a, b, c: self.set_modified())

		self.modifycallback = modifycallback
		self.deletecallback = deletecallback

		buttons = Frame(self)
		buttons.grid(row=3, columnspan=2, sticky=NSEW)

		self.modify = Button(buttons, text="Modify", command=self.modify)
		self.modify.pack(side=RIGHT, pady=5)
		self.delete = Button(buttons, text="Delete", command=self.delete)
		self.delete.pack(side=RIGHT, padx=5, pady=5)

		self.booking = None

	def set_modified(self, modified=True):
		self.modified = modified
		self.modify["state"] = NORMAL if self.modified else DISABLED

	def modify(self):
		table_id = self.get_table_id()
		if table_id == -1: return

		arrival = self.get_arrival()
		if arrival == -1: return

		self.booking["table_id"] = table_id
		self.booking["arrival"] = arrival

		self.modifycallback(self.booking)
		self.set_modified(False)

	def delete(self):
		self.deletecallback(self.booking)
		self.load(None)

	def load(self, booking):
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

class BookingManager(Frame):
	def __init__(self, master=None):
		Frame.__init__(self, master)

		panes = PanedWindow(self, sashwidth=5, sashrelief=RAISED, sashpad=5)
		panes.grid(padx=5, pady=5, sticky=NSEW)

		self.bookings = Listbox(panes)
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
		self.bookings.delete(0, END)
		self.booking_ids.clear()

		for booking in bookings.values():
			self.bookings.insert(END, booking["booking_id"])
			self.booking_ids.append(booking["booking_id"])

	# Callbacks for different forms

	def booking_added(self, booking):
		cursor.execute(ADD_BOOKING, (booking["table_id"], booking["arrival"]))
		database.commit()

		booking["booking_id"] = last_id()
		bookings[booking["booking_id"]] = booking

		self.populate_list()

	def booking_modified(self, booking):
		cursor.execute(MODIFY_BOOKING, (booking["table_id"], booking["arrival"], booking["booking_id"]))

		database.commit()
		self.populate_list()

	def booking_deleted(self, booking):
		cursor.execute(DELETE_EMPLOYEE, (booking["booking_id"], ))
		database.commit()

		del bookings[booking["booking_id"]]
		self.populate_list()

	# End callbacks

	def init_forms(self, panes):
		forms = Frame(panes)
		forms.columnconfigure(0, weight=1)

		self.add_booking  = AddBooking(self.booking_added, forms)
		self.edit_booking = EditBooking(self.booking_modified, self.booking_deleted, forms)

		self.add_booking.grid(row=1, sticky=EW)
		self.edit_booking.grid(row=2, sticky=EW)

		panes.add(forms)

	def select(self, event=None):
		booking = self.bookings.curselection()
		if booking:
			self.edit_booking.grid()

			booking = bookings[self.booking_ids[booking[0]]]
			self.edit_booking.load(booking)
		else:
			self.edit_booking.grid_remove()
