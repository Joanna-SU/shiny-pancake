import data, util, tkinter, sqlite3
from constants import *

member = None # The currently logged in member

def can_login(member_id, password):
	salt = data.get_salt(member_id)
	password = data.hash(password, salt)

	data.cursor.execute(data.CAN_LOGIN, (sqlite3.Binary(password), member_id))
	return bool(data.cursor.fetchone()[0])

class LoginForm(tkinter.Frame):
	def __init__(self, callback, master=None):
		tkinter.Frame.__init__(self, master)
		self.callback = callback

		tkinter.Label(self, text="User ID").grid(row=0, sticky=E)
		self.name = tkinter.Entry(self)
		self.name.grid(row=0, column=1, sticky=EW)

		tkinter.Label(self, text="Password").grid(row=1, sticky=E)
		self.password = tkinter.Entry(self, show=MASK)
		self.password.grid(row=1, column=1, sticky=EW)

		self.submit = tkinter.Button(self, text="Log In", command=self.login)
		self.submit.grid(row=2, column=0, columnspan=2, pady=5, sticky=E)

		self.columnconfigure(1, weight=1)
		self.columnconfigure(2, weight=2)

		# Pressing enter submits the form
		self.name.bind("<Return>", self.login)
		self.password.bind("<Return>", self.login)
		self.submit.bind("<Return>", self.login)

	def login(self, e=None):
		"""Processes submitting the login form"""
		name = self.name.get()
		# Need to have an ID to look up in the db
		if not name.isnumeric():
			member_id = util.find_by_name(name)
		else:
			member_id = int(name)

		if member_id in data.members:
			member = data.members[member_id]

			if can_login(member_id, self.password.get()):
				self.callback(member)
				tkinter.messagebox.showinfo("Login Successful", "You are now logged in as {}, member ID {}".format(util.unique_name(member), member["member_id"]))
				# A successful login clears the name field
				self.name.delete(0, END)
			else:
				tkinter.messagebox.showerror("Login failed", "Invalid password for {first_name} {last_name}.".format(**member))
		else:
			tkinter.messagebox.showerror("Login failed", "Member \"{}\" not found.".format(self.name.get()))
		# Both successful and unsuccessful logins clear the password field
		self.password.delete(0, END)
