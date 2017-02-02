from tkinter import *
from tkinter import messagebox
from constants import *
from login import *
from member import *
from data import *
from floorplan import *

class MainWindow(Frame):
	def __init__(self, master=None):
		Frame.__init__(self, master)
		self.master.title("Restaurant Manager")
		self.master.iconbitmap("icon.ico")

		# Set up resizable window
		self.master.columnconfigure(0, weight=1)
		self.master.rowconfigure(0, weight=1)
		self.master.geometry("800x600")

		self.init_menu()
		self.init_topbar()
		self.frames = []
		self.init_frames()

		self.login() # Updates login status to not logged in
		self.frame(CHOOSE_OPTION)
		self.menu_button() # Show menu

		self.grid(sticky=NSEW, padx=5, pady=5)

	def login(self, user=None):
		self.user = user

		if user:
			self.buttons[LOGIN]["state"] = self.frames[LOGIN].submit["state"] = DISABLED
			self.logged["text"] = LOGGED.format(user["first_name"])
			self.loginbutton["text"] = LOGOUT_TAG
			self.loginbutton["command"] = self.login
		else:
			self.buttons[LOGIN]["state"] = self.frames[LOGIN].submit["state"] = NORMAL
			self.logged["text"] = NOT_LOGGED
			self.loginbutton["text"] = LOGIN_TAG
			self.loginbutton["command"] = lambda: self.frame(0)

			if self.buttons[ADD_MEMBER]["relief"] == SUNKEN \
					or self.buttons[BOOKINGS]["relief"] == SUNKEN:
				# Switch to a valid page
				self.frame(LOGIN)

		permission = user and user["permission"]
		state = NORMAL if permission else DISABLED

		self.buttons[ADD_MEMBER]["state"]     = state
		self.buttons[BOOKINGS]["state"]       = state
		self.frames[FLOOR_PLAN].edit["state"] = state

		if not permission: # Make sure we're not editing already
			self.frames[FLOOR_PLAN].set_editing(False)

		self.loginbutton["state"] = NORMAL

	def frame(self, frame):
		# Selects a frame by bringing it to the front
		self.frames[frame].lift()

		if frame != CHOOSE_OPTION:
			self.framewrapper["text"] = BUTTONS[frame]

			# Display correct button as selected
			for button in self.buttons:
				button["relief"] = SUNKEN if button is self.buttons[frame] else RAISED
			# Close the menu if it's open
			if self.menubutton["relief"] == SUNKEN:
				self.menu_button()

	def init_topbar(self):
		self.topbar = Frame(self, border=1, relief=SUNKEN)
		self.logged = Label(self.topbar)
		self.loginbutton = Button(self.topbar, text="Log In")

		self.logged.pack(side="left")
		self.loginbutton.pack(side="left")
		self.topbar.grid(row=0, column=0, padx=2, pady=2, ipadx=2, ipady=2, sticky=E)

	def menu_button(self):
		if self.menubutton["relief"] == RAISED: # Enable
			self.menubutton["relief"] = SUNKEN
			self.menu.lift()
		else:                                   # Disable
			self.menubutton["relief"] = RAISED
			self.menu.lower()

	def init_menu(self):
		self.menu = Frame(self)
		self.menu.configure(background="white", relief=RAISED, border=1)

		self.menu.rowconfigure(0, minsize=20)
		self.menu.rowconfigure(len(BUTTONS)+1, minsize=20)
		self.menu.columnconfigure(0, minsize=50)
		self.menu.columnconfigure(2, minsize=50)

		self.buttons = []
		for i in range(len(BUTTONS)):
			self.buttons.append(Button(self.menu, text=BUTTONS[i],
				command=lambda i=i: self.frame(i)))
			self.buttons[i].grid(row=i+1, column=1, sticky=NSEW, pady=2)

		self.menu.place(relx=0.5, rely=0.5, anchor=CENTER)
		self.menu.lower()

		# Menu button
		self.menubutton = Button(self, text="Menu", command=self.menu_button)
		self.menubutton.grid(row=0, column=0, sticky=W)

	def init_frames(self):
		self.columnconfigure(0, weight=1)
		self.rowconfigure(2, weight=1)
		self.framewrapper = LabelFrame(self, padx=5, pady=5)
		self.framewrapper.grid(row=2, sticky=NSEW)

		self.framewrapper.rowconfigure(0, weight=1)
		self.framewrapper.columnconfigure(0, weight=1)

		# Create the actual frames
		self.frames.append(LoginForm(self.login, self.framewrapper))
		self.frames.append(MemberManager(self.login, self.framewrapper))
		self.frames.append(Label(self.framewrapper, text="[bookings]"))
		self.frames.append(FloorPlan(self.framewrapper))

		self.frames.append(Label(self.framewrapper, text="Choose a menu option", relief=SUNKEN, bg="#DDD"))

		# Overlap all the frames on one another
		for frame in self.frames:
			frame.grid(row=0, column=0, sticky=NSEW)

init_db()
load_members()
window = MainWindow()

# Handle first time admin login
if len(members) == 0:
	window.login({"first_name": "administrator", "permission": True}) # Default admin
	window.loginbutton["state"] = DISABLED

	window.frames[ADD_MEMBER].add_member.admin.set(True)
	window.frames[ADD_MEMBER].add_member.admin_button["state"] = DISABLED

	messagebox.showinfo("First time run",
		"As there are no staff members, you have been logged in as the default administrator.\n" \
		"You can add staff members in the member manager.\n\n" \
		"Make sure you do not forget all the admin passwords, as you will no longer be able to log in.")

window.mainloop()
cleanup_db()
