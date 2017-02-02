from tkinter import *
from data import *
from constants import *
import os, sqlite3

# Probably shouldn't do this
import __main__

class MemberForm(LabelFrame):
	def __init__(self, add_id, master=None, text=None):
		LabelFrame.__init__(self, master, text=text)
		self.columnconfigure(1, weight=1)
		self.columnconfigure(2, weight=2, minsize=100)

		self.fields = {}

		for i in range(not add_id, len(FIELDS)):
			Label(self, text=FIELDS[i][1]).grid(row=i, sticky=E)
			self.fields[FIELDS[i][0]] = Entry(self)
			self.fields[FIELDS[i][0]].grid(row=i, column=1, sticky=EW)

		self.admin = IntVar()
		self.admin_button = Checkbutton(self, text="Admin", variable=self.admin)
		self.admin_button.grid(row=len(FIELDS), column=1, sticky=W)

		if add_id:
			self.fields["member_id"].insert(0, "0")
			self.fields["member_id"]["state"] = "readonly"

	def set_show(self, show):
		self.fields["password"]["show"] = "" if show else MASK

	def clear_fields(self):
		if "member_id" in self.fields:
			self.fields["member_id"]["state"] = NORMAL
		for field in self.fields:
			self.fields[field].delete(0, END)
		if "member_id" in self.fields:
			self.fields["member_id"]["state"] = "readonly"

		self.admin.set(False)

	def load_member(self, member):
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

		self.submit = Button(self, text="Add", command=self.add)
		self.submit.grid(row=6, columnspan=2, pady=5, sticky=E)

	def add(self):
		user = {field: self.fields[field].get() for field in self.fields}
		user["permission"] = self.admin.get()
		self.addcallback(user)
		self.clear_fields()

class EditMember(MemberForm):
	def __init__(self, modifycallback, deletecallback, master=None):
		MemberForm.__init__(self, True, master)

		self.vars = {field: StringVar() for field in self.fields}
		for key in self.vars:
			if key == "password":
				self.vars[key].trace("w", self.on_write_pw)
				self.pwhint = Label(self, text="(unmodified)")
				self.pwhint.grid(row=4, column=2, sticky=W)
			else:
				self.vars[key].trace("w", lambda a, b, c: self.set_modified())

			self.fields[key]["textvariable"] = self.vars[key]
		self.admin.trace("w", lambda a, b, c: self.set_modified())

		self.modifycallback = modifycallback
		self.deletecallback = deletecallback

		buttons = Frame(self)
		buttons.grid(row=6, columnspan=2, sticky=NSEW)

		self.modify = Button(buttons, text="Modify", command=self.modify)
		self.modify.pack(side=RIGHT, pady=5)
		self.delete = Button(buttons, text="Delete", command=self.delete)
		self.delete.pack(side=RIGHT, padx=5, pady=5)

		self.member = None

	def on_write_pw(self, name, index, operation):
		modified = len(self.vars["password"].get()) > 0

		self.set_modified(modified, True)
		if modified:
			self.pwhint.grid_remove()
		else:
			self.pwhint.grid()

	def set_modified(self, modified=True, pw=False):
		self.pwmodified = modified
		if not pw:
			self.modified = modified

		self.modify["state"] = NORMAL if self.modified or self.pwmodified else DISABLED

	def modify(self):
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
		if self.member and self.modified:
			if not messagebox.askyesno("Are you sure?",
					"You have made changes to {}.\nAre you sure you want to " \
					"discard these changes?".format(self.member)):
				return False
		self.clear_fields()
		if member: self.load_member(member)

		self["text"] = ("Edit " + member["first_name"]) if member else None
		self.member = member
		self.set_modified(False)

		# Can't remove admin from yourself, or delete yourself
		self.delete["state"] = self.admin_button["state"] = DISABLED if self.member == __main__.window.user else NORMAL

		return True

class MemberManager(Frame):
	def __init__(self, login_callback, master=None):
		Frame.__init__(self, master)
		self.login_callback = login_callback

		panes = PanedWindow(self, sashwidth=5, sashrelief=RAISED, sashpad=5)
		panes.grid(padx=5, pady=5, sticky=NSEW)

		self.members = Listbox(panes)
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
		self.members.delete(0, END)
		self.member_ids.clear()

		for member in members.values():
			self.members.insert(END, member["first_name"])
			self.member_ids.append(member["member_id"])

	# Callbacks for different forms

	def user_added(self, user):
		salt = gen_salt()
		password = hash(user["password"], salt)
		cursor.execute(ADD_EMPLOYEE, (user["first_name"], user["last_name"], user["phone_number"], user["permission"], sqlite3.Binary(password), sqlite3.Binary(salt)))
		database.commit()

		user["member_id"] = last_id()
		user["password"] = ""
		members[user["member_id"]] = user

		if len(members) == 1: # Can log out from default admin
			self.login_callback(user)
			self.add_member.admin_button["state"] = NORMAL

		self.populate_list()

	def user_modified(self, user):
		cursor.execute(MODIFY_EMPLOYEE, (user["first_name"], user["last_name"], user["phone_number"], user["permission"], user["member_id"]))

		# Updates the user's password, when necessary
		if user["password"]:
			salt = gen_salt()
			password = hash(user["password"], salt)
			cursor.execute(MODIFY_PASSWORD, (sqlite3.Binary(password), sqlite3.Binary(salt), user["member_id"]))

			user["password"] = ""

		database.commit()
		self.populate_list()

	def user_deleted(self, user):
		cursor.execute(DELETE_EMPLOYEE, (user["member_id"], ))
		database.commit()

		del members[user["member_id"]]
		self.populate_list()

	# End callbacks

	def set_show(self):
		show = self.toggle.get()
		self.add_member.set_show(show)
		self.edit_member.set_show(show)

	def init_forms(self, panes):
		forms = Frame(panes)
		forms.columnconfigure(0, weight=1)

		self.toggle = IntVar()
		Checkbutton(forms, text="Show passwords", variable=self.toggle, command=self.set_show).grid(columnspan=2, sticky=E)

		self.add_member  = AddMember(self.user_added, forms)
		self.edit_member = EditMember(self.user_modified, self.user_deleted, forms)

		self.add_member.grid(row=1, sticky=EW)
		self.edit_member.grid(row=2, sticky=EW)

		panes.add(forms)

	def select(self, event=None):
		user = self.members.curselection()
		if user:
			self.edit_member.grid()

			user = members[self.member_ids[user[0]]]
			self.edit_member.load(user)
		else:
			self.edit_member.grid_remove()
