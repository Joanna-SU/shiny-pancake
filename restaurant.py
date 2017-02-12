import login, member, booking, floorplan, data, util, tkinter, tkinter.messagebox
from constants import *

class MainWindow(tkinter.Frame):
	def __init__(self, master=None):
		tkinter.Frame.__init__(self, master)
		self.master.title("Restaurant Manager")
		self.master.iconbitmap("icon.ico")

		# Set up resizable window
		self.master.columnconfigure(0, weight=1)
		self.master.rowconfigure(0, weight=1)
		self.grid(sticky=NSEW, padx=5, pady=5)
		self.master.geometry("800x600")

		self.init_frames()
		self.init_menu()

		self.login() # Updates login status to not logged in
		self.selected = LOGIN

	def login(self, member=None):
		"""Sets the system-wide logged in member to the given member"""
		self.present_button["state"] = NORMAL
		login.member = member

		if member:
			self.buttons[LOGIN]["state"]       = DISABLED
			self.frames[LOGIN].submit["state"] = DISABLED

			self.logged["text"] = LOGGED.format(util.unique_name(member))
			self.loginbutton["text"] = LOGOUT_TAG
			self.loginbutton["command"] = self.login
			self.frames[ADD_MEMBER].select() # Prevent deleting yourself

			permission = member["permission"]
			self.present.set(member["present"])
		else:
			self.buttons[LOGIN]["state"]       = NORMAL
			self.frames[LOGIN].submit["state"] = NORMAL

			self.logged["text"] = NOT_LOGGED
			self.loginbutton["text"] = LOGIN_TAG
			self.loginbutton["command"] = lambda: self.frame(LOGIN)

			if self.buttons[ADD_MEMBER]["relief"] == SUNKEN \
					or self.buttons[BOOKINGS]["relief"] == SUNKEN:
				# Switch to a valid page
				self.frame(LOGIN)

			permission = False
			self.present.set(False)
			self.present_button["state"] = DISABLED

		state = NORMAL if permission else DISABLED
		self.buttons[ADD_MEMBER]["state"]     = state
		self.buttons[BOOKINGS]["state"]       = state
		self.frames[FLOOR_PLAN].edit["state"] = state

		if not permission: # Make sure we're not editing already
			self.frames[FLOOR_PLAN].set_editing(False)

		self.loginbutton["state"] = NORMAL

	def frame(self, frame):
		"""Selects a frame by bringing it to the front"""
		self.buttons[self.selected]["relief"] = RAISED
		self.buttons[frame]["relief"] = SUNKEN

		# Close the menu if it's open
		if self.menubutton["relief"] == SUNKEN:
			self.toggle_menu()

		self.selected = frame
		self.frames[frame].lift()
		self.framewrapper["text"] = BUTTONS[frame]

	def mark_present(self):
		"""Updates the cache and database with the present status"""
		if login.member:
			logout = login.member["present"] and not self.present.get() \
				and tkinter.messagebox.askyesno("Log out?", "You have been marked as not present. Do you want to log out?")

			login.member["present"] = self.present.get()
			data.cursor.execute(data.MARK_PRESENT, (login.member["present"], login.member["member_id"]))
			data.database.commit()

			if logout: self.login()

	def init_menu(self):
		"""Initializes the menu and login frames"""
		# Present toggle
		self.present = tkinter.IntVar()
		self.present_button = tkinter.Checkbutton(self, text="Present", variable=self.present)
		self.present_button.grid(row=0, column=0, sticky=EW)
		self.present.trace("w", lambda a, b, c: self.mark_present())

		# Login status
		loginbar = tkinter.Frame(self, border=1, relief=SUNKEN)
		self.logged = tkinter.Label(loginbar)
		self.loginbutton = tkinter.Button(loginbar, text="Log In")

		self.logged.pack(side="left")
		self.loginbutton.pack(side="left")
		loginbar.grid(row=0, column=0, padx=2, pady=2, ipadx=2, ipady=2, sticky=E)

		# Menu
		self.menu = tkinter.Frame(self)
		self.menu.configure(background="white", relief=RAISED, border=1)

		self.menu.rowconfigure(0, minsize=20)
		self.menu.rowconfigure(len(BUTTONS)+1, minsize=20)
		self.menu.columnconfigure(0, minsize=50)
		self.menu.columnconfigure(2, minsize=50)

		self.buttons = []
		for i in range(len(BUTTONS)):
			self.buttons.append(tkinter.Button(self.menu, text=BUTTONS[i],
				command=lambda i=i: self.frame(i)))
			self.buttons[i].grid(row=i+1, column=1, sticky=NSEW, pady=2)

		self.menu.place(relx=0.5, rely=0.5, anchor=CENTER)

		# Menu button
		self.menubutton = tkinter.Button(self, text="Menu", command=self.toggle_menu, relief=SUNKEN)
		self.menubutton.grid(row=0, column=0, sticky=W)

	def toggle_menu(self):
		if self.menubutton["relief"] == RAISED: # Enable
			self.menubutton["relief"] = SUNKEN
			self.menu.lift()
		else: # Disable
			self.menubutton["relief"] = RAISED
			self.menu.lower()

	def init_frames(self):
		"""Initializes the different pages of the UI"""
		self.columnconfigure(0, weight=1)
		self.rowconfigure(2, weight=1)
		self.framewrapper = tkinter.LabelFrame(self, padx=5, pady=5)
		self.framewrapper.grid(row=2, sticky=NSEW)

		self.framewrapper.rowconfigure(0, weight=1)
		self.framewrapper.columnconfigure(0, weight=1)

		# Create the actual frames
		bookings = booking.BookingManager(self.framewrapper)
		self.frames = [
			login.LoginForm(self.login, self.framewrapper),
			member.MemberManager(self.login, self.framewrapper),
			bookings,
			floorplan.FloorPlan(bookings.populate_tables, self.framewrapper),
			tkinter.Label(self.framewrapper, text="Choose a menu option",
				relief=SUNKEN, bg="#DDD")
		]

		# Overlap all the frames on one another
		for frame in self.frames:
			frame.grid(row=0, column=0, sticky=NSEW)

data.init_db()
window = MainWindow()

# Logs in as 'default' admin when there are no existing admins
if len(data.members) == 0:
	# The simplest admin account possible, doesn't exist in database
	window.login({"first_name": "administrator", "permission": True})
	window.loginbutton["state"] = DISABLED

	window.frames[ADD_MEMBER].add_member.admin.set(True)
	window.frames[ADD_MEMBER].add_member.admin_button["state"] = DISABLED

	tkinter.messagebox.showinfo("First time run",
		"As there are no staff members, you have been logged in as the default administrator.\n" \
		"You can add staff members in the member manager.\n\n" \
		"Make sure you do not forget all the admin passwords, as you will no longer be able to log in.")

window.mainloop()
data.cleanup_db()
