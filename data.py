import sqlite3, os, hashlib
from constants import *

# Pre-defined SQL statements

ADD_EMPLOYEE    = "INSERT INTO staff " \
                  "(first_name, last_name, phone_number, permission, password, salt) " \
                  "VALUES (?, ?, ?, ?, ?, ?);"

MODIFY_EMPLOYEE = "UPDATE staff " \
                  "SET first_name=?, last_name=?, phone_number=?, permission=? " \
                  "WHERE member_id=?;"

MODIFY_PASSWORD = "UPDATE staff " \
                  "SET password=?, salt=? " \
                  "WHERE member_id=?;"

DELETE_EMPLOYEE = "DELETE FROM staff " \
                  "WHERE member_id=?;"

LIST_EMPLOYEES  = "SELECT member_id, first_name, last_name, phone_number, permission " \
                  "FROM staff " \
                  "ORDER BY first_name;"

GET_SALT        = "SELECT salt FROM staff WHERE member_id=?"
CAN_LOGIN       = "SELECT CASE WHEN password=? THEN 1 ELSE 0 END " \
                  "FROM staff " \
                  "WHERE member_id=?;"

ADD_TABLE       = "INSERT INTO layout_table " \
                  "(table_number, capacity, x_pos, y_pos, width, height, shape) " \
                  "VALUES (?, ?, ?, ?, ?, ?, ?);"

DELETE_TABLE    = "DELETE FROM layout_table " \
                  "WHERE table_id=?;"

MODIFY_TABLE    = "UPDATE layout_table " \
                  "SET table_number=?, capacity=?, x_pos=?, y_pos=?, width=?, height=?, shape=? " \
                  "WHERE table_id=?;"

LIST_TABLES     = "SELECT * " \
                  "FROM layout_table;"

ADD_BOOKING     = "INSERT INTO booking " \
                  "(customer, table_id, arrival) " \
                  "VALUES (?, ?, ?);"

MODIFY_BOOKING  = "UPDATE booking " \
                  "SET customer=?, table_id=?, arrival=? " \
                  "WHERE booking_id=?;"

DELETE_BOOKING  = "DELETE FROM booking " \
                  "WHERE booking_id=?;"

LIST_BOOKINGS   = "SELECT * " \
                  "FROM booking;"

SET_STATUS      = "UPDATE booking " \
                  "SET status=? " \
                  "WHERE booking_id=?;"

# Hashes and salts are all handled as bytes objects

def hash(password, salt):
	"""Generates a hashed password for storing in the database"""
	return hashlib.sha256(password.encode("utf-8") + salt).digest()

def get_salt(member_id):
	"""Grabs salt for the given member from the database"""
	cursor.execute(GET_SALT, (member_id, ))
	return bytes(cursor.fetchone()[0])

def gen_salt():
	"""Generates a salt for use with hashing to prevent rainbow table use"""
	return os.urandom(16)

# Global database access
database = sqlite3.connect(DATABASE)
cursor   = database.cursor()

def init_db():
	"""Handles loading all the data the program needs from the database"""
	with open("setup.sql", "r") as script:
		database.executescript(script.read())
	load_members()
	load_tables()
	load_bookings()

def cleanup_db():
	cursor.close()
	database.close()

# Caches of members, tables and bookings

members = {}
current_work = {}

def load_members():
	"""Populates the cache of members from the database"""
	global members
	cursor.execute(LIST_EMPLOYEES)

	members.clear()
	for row in cursor.fetchall():
		members[row[0]] = {
			"permission": row[-1]
		}
		for i in range(4): # Copy fields directly one at a time
			members[row[0]][FIELDS[i][0]] = row[i]

	current_work.update({id: 0 for id in members})

tables = {}
def load_tables():
	"""Populates the cache of tables from the database"""
	global tables
	cursor.execute(LIST_TABLES)

	tables.clear()
	for row in cursor.fetchall():
		tables[row[0]] = {
			"table_id": row[0],
			"shape": row[-1] # Last item is shape
		}
		for i in range(1, len(row)-1): # Remaining fields
			tables[row[0]][TABLE_FIELDS[i-1][0]] = row[i]

bookings = {}
def load_bookings():
	"""Populates the cache of bookings from the database"""
	global bookings
	cursor.execute(LIST_BOOKINGS)

	bookings.clear()
	for row in cursor.fetchall():
		bookings[row[0]] = {
			"booking_id":  row[0],
			"customer":   row[1],
			"member_id": row[2],
			"table_id": row[3],
			"arrival": row[4],
			"status": row[5],
			"ping":  row[6]
		}
