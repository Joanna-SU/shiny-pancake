from tkinter import *
from tkinter import messagebox
from data import *
from util import validate_digits
from constants import MASK
import hashlib, sqlite3

def find_by_name(name):
	"""Finds the member that most closely matches the given name.

	For example, "sam" will more closely match "samuel" than "s".
	The comparison is case-insensitive."""
	max_match = 0
	max_member = None

	for key in members:
		member_name = members[key]["first_name"] + " " + members[key]["last_name"]

		if len(member_name) < max_match: # Can't possibly be closest
			continue

		match = 0
		while match < len(member_name) and match < len(name):
			if member_name[match].lower() != name[match].lower():
				break
			match += 1

		if match > max_match:
			max_match = match
			max_member = key

	return max_member if max_member else -1

def can_login(username, password):
	salt = get_salt(username)
	password = hash(password, salt)
	cursor.execute(CAN_LOGIN, (sqlite3.Binary(password), username))

	return bool(cursor.fetchone()[0])

class LoginForm(Frame):
	def __init__(self, callback, master=None):
		Frame.__init__(self, master)
		self.callback = callback

		Label(self, text="User ID").grid(row=0, sticky=E)
		Label(self, text="Password").grid(row=1, sticky=E)

		self.user_id = Entry(self)
		self.user_id.grid(row=0, column=1, sticky=EW)

		self.password = Entry(self, show=MASK)
		self.password.grid(row=1, column=1, sticky=EW)

		self.submit = Button(self, text="Log In", command=self.login)
		self.submit.grid(row=2, column=0, columnspan=2, pady=5, sticky=E)

		self.columnconfigure(1, weight=1)
		self.columnconfigure(2, weight=2)

	def login(self):
		user_raw = self.user_id.get()
		if not user_raw.isnumeric():
			user_id = find_by_name(user_raw)
		else:
			user_id = int(user_raw)

		if user_id in members:
			user = members[user_id]

			if can_login(user_id, self.password.get()):
				self.callback(user)
				messagebox.showinfo("Login Successful", "You are now logged in as {first_name}, user ID {member_id}".format(**user))
				self.user_id.delete(0, END)
			else:
				messagebox.showerror("Login failed", "Invalid password for {first_name} {last_name}.".format(**user))
		else:
			messagebox.showerror("Login failed", "User \"{}\" not found.".format(self.user_id.get()))
		self.password.delete(0, END)
