import login, data, tkinter, sqlite3
from constants import *

class MemberForm(tkinter.LabelFrame):
	def __init__(self, add_id, master=None, text=None):
		tkinter.LabelFrame.__init__(self, master, text=text)
		self.columnconfigure(1, weight=1)
		self.columnconfigure(2, weight=2, minsize=100)

		self.fields = {}

		# Start at row 1 if not adding the ID
		for i in range(not add_id, len(FIELDS)):
			tkinter.Label(self, text=FIELDS[i][1]).grid(row=i, sticky=E)
			self.fields[FIELDS[i][0]] = tkinter.Entry(self)
			self.fields[FIELDS[i][0]].grid(row=i, column=1, sticky=EW)

		self.admin = tkinter.IntVar()
		self.admin_button = tkinter.Checkbutton(self, text="Admin", variable=self.admin)
		self.admin_button.grid(row=len(FIELDS), column=1, sticky=W)

		if add_id: # Prevent modification of the ID field
			self.fields["member_id"].insert(0, "0")
			self.fields["member_id"]["state"] = "readonly"

	def set_show(self, show):
		"""Show or hide the data in the password field"""
		self.fields["password"]["show"] = "" if show else MASK

	def clear_fields(self):
		"""Clears the information from all the fields in the form"""
		if "member_id" in self.fields:
			self.fields["member_id"]["state"] = NORMAL
		for field in self.fields:
			self.fields[field].delete(0, END)
		if "member_id" in self.fields:
			self.fields["member_id"]["state"] = "readonly"

		self.admin.set(False)

	def load_member(self, member):
		"""Loads the information from the member into the form"""
		if "member_id" in self.fields:
			self.fields["member_id"]["state"] = NORMAL
		for field in self.fields:
			if field in member:
				self.fields[field].insert(0, member[field])
		if "member_id" in self.fields:
			self.fields["member_id"]["state"] = "readonly"

		self.admin.set(member["permission"])

class AddMember(MemberForm):
	def __init__(self, addcallback, master=None):
		MemberForm.__init__(self, False, master, "Add a Member")
		self.addcallback = addcallback

		self.submit = tkinter.Button(self, text="Add", command=self.add)
		self.submit.grid(row=6, columnspan=2, pady=5, sticky=E)

	def add(self):
		"""Processes submitting the form"""
		member = {field: self.fields[field].get() for field in self.fields}
		member["permission"] = self.admin.get()
		# People's names are always capitalized
		member["first_name"] = member["first_name"].capitalize()
		member["last_name"] = member["last_name"].capitalize()
		self.addcallback(member)
		self.clear_fields()

class EditMember(MemberForm):
	def __init__(self, modifycallback, deletecallback, master=None):
		MemberForm.__init__(self, True, master)

		# Set up variables to track changes
		self.vars = {field: tkinter.StringVar() for field in self.fields}
		for key in self.vars:
			if key == "password": # Password is only modified if not empty
				self.vars[key].trace("w", self.on_write_pw)
				self.pwhint = tkinter.Label(self, text="(unmodified)")
				self.pwhint.grid(row=4, column=2, sticky=W)
			else:
				self.vars[key].trace("w", lambda a, b, c: self.set_modified())

			self.fields[key]["textvariable"] = self.vars[key]
		self.admin.trace("w", lambda a, b, c: self.set_modified())

		# Callbacks to update the database
		self.modifycallback = modifycallback
		self.deletecallback = deletecallback

		buttons = tkinter.Frame(self)
		buttons.grid(row=6, columnspan=2, sticky=NSEW)

		self.modify = tkinter.Button(buttons, text="Modify", command=self.modify)
		self.modify.pack(side=RIGHT, pady=5)
		self.delete = tkinter.Button(buttons, text="Delete", command=self.delete)
		self.delete.pack(side=RIGHT, padx=5, pady=5)

		self.member = None

	def on_write_pw(self, name, index, operation):
		"""Event handler for password field changed"""
		modified = len(self.vars["password"].get()) > 0

		self.set_modified(modified, True)
		if modified:
			self.pwhint.grid_remove()
		else:
			self.pwhint.grid()

	def set_modified(self, modified=True, pw=False):
		"""Event handler for other fields changed"""
		self.pwmodified = modified
		if not pw:
			self.modified = modified

		self.modify["state"] = NORMAL if self.modified or self.pwmodified else DISABLED

	def modify(self):
		"""Processes modifying a member (clicking the modify button)"""
		for field in self.fields:
			if field != "member_id":
				self.member[field] = self.fields[field].get()
		self.member["permission"] = self.admin.get()

		self.modifycallback(self.member)
		self.fields["password"].delete(0, END)
		self.set_modified(False)

	def delete(self):
		self.deletecallback(self.member)
		self.load(None)

	def load(self, member):
		"""Displays the information of a member when selected"""
		if self.member and self.modified:
			if not messagebox.askyesno("Are you sure?",
					"You have made changes to {}.\nAre you sure you want to " \
					"discard these changes?".format(self.member["first_name"])):
				return False
		self.clear_fields()
		if member: self.load_member(member)

		self["text"] = ("Edit " + member["first_name"]) if member else None
		self.member = member
		self.set_modified(False)

		# Can't remove admin from yourself, or delete yourself
		self.delete["state"] = self.admin_button["state"] = DISABLED if self.member == login.member else NORMAL

		return True

class MemberManager(tkinter.Frame):
	def __init__(self, login_callback, master=None):
		tkinter.Frame.__init__(self, master)
		self.login_callback = login_callback

		panes = tkinter.PanedWindow(self, sashwidth=5, sashrelief=RAISED, sashpad=5)
		panes.grid(padx=5, pady=5, sticky=NSEW)

		# Left pane, list of members
		self.members = tkinter.Listbox(panes)
		self.member_ids = []

		self.populate_list()
		self.members.bind("<<ListboxSelect>>", self.select)
		panes.add(self.members)

		self.init_forms(panes)

		self.rowconfigure(0, weight=1)
		self.columnconfigure(0, weight=1)
		self.select()
		self.set_show()

	def populate_list(self):
		"""Grabs members from the database cache and adds them to the list"""
		self.members.delete(0, END)
		self.member_ids.clear()

		for member in data.members.values():
			self.members.insert(END, member["first_name"])
			self.member_ids.append(member["member_id"])

	# Callbacks for different forms

	def member_added(self, member):
		"""Adds a new member to the database"""
		salt = data.gen_salt()
		password = data.hash(member["password"], salt)
		data.cursor.execute(data.ADD_EMPLOYEE, (member["first_name"], member["last_name"], member["phone_number"], member["permission"], sqlite3.Binary(password), sqlite3.Binary(salt)))
		data.database.commit()

		member["member_id"] = data.cursor.lastrowid
		member["password"] = ""
		data.members[member["member_id"]] = member
		data.current_work[member["member_id"]] = 0

		if len(data.members) == 1: # Can log out from default admin
			self.login_callback(member)
			self.add_member.admin_button["state"] = NORMAL

		self.populate_list()

	def member_modified(self, member):
		"""Updates the given member with the new information"""
		data.cursor.execute(data.MODIFY_EMPLOYEE, (member["first_name"], member["last_name"], member["phone_number"], member["permission"], member["member_id"]))

		# Updates the member's password, when necessary
		if member["password"]:
			salt = data.gen_salt()
			password = data.hash(member["password"], salt)
			data.cursor.execute(data.MODIFY_PASSWORD, (sqlite3.Binary(password), sqlite3.Binary(salt), member["member_id"]))

			member["password"] = ""

		data.database.commit()
		self.populate_list()

	def member_deleted(self, member):
		"""Removes a member from the database"""
		data.cursor.execute(data.DELETE_EMPLOYEE, (member["member_id"], ))
		data.database.commit()

		del data.members[member["member_id"]]
		del data.current_work[member["member_id"]]
		self.populate_list()
		self.select()

	# End callbacks

	def set_show(self):
		"""Updates the visibility status of both forms' password fields"""
		show = self.toggle.get()
		self.add_member.set_show(show)
		self.edit_member.set_show(show)

	def init_forms(self, panes):
		"""Initializes the add and edit member forms"""
		forms = tkinter.Frame(panes)
		forms.columnconfigure(0, weight=1)

		self.toggle = tkinter.IntVar()
		tkinter.Checkbutton(forms, text="Show passwords", variable=self.toggle, command=self.set_show).grid(columnspan=2, sticky=E)

		self.add_member  = AddMember(self.member_added, forms)
		self.edit_member = EditMember(self.member_modified, self.member_deleted, forms)

		self.add_member.grid(row=1, sticky=EW)
		self.edit_member.grid(row=2, sticky=EW)

		panes.add(forms)

	def select(self, event=None):
		"""Shows and hides the edit member form when necessary"""
		member = self.members.curselection()
		if member:
			self.edit_member.grid()

			member = data.members[self.member_ids[member[0]]]
			self.edit_member.load(member)
		else:
			self.edit_member.grid_remove()
