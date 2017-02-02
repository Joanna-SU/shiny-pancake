LOGIN = 0
ADD_MEMBER = 1
BOOKINGS = 2
FLOOR_PLAN = 3
CHOOSE_OPTION = 4

BUTTONS = ["Log In", "Member Manager", "Booking Manager", "Floor Plan Manager"]
FIELDS  = (
	("member_id", "ID"),
	("first_name", "First Name"),
	("last_name", "Last Name"),
	("phone_number", "Phone Number"),
	("password", "Password")
)
TABLE_FIELDS = (
	("table_number", "Table Number"),
	("capacity", "Capacity"),
	("x_pos", "X Position"),
	("y_pos", "Y Position"),
	("width", "Width"),
	("height", "Height")
)

NOT_LOGGED   = "Not logged in"
LOGGED       = "Logged in as {}"
LOGIN_TAG    = "Log In"
LOGOUT_TAG   = "Log Out"
MASK         = "\u2022"
DATABASE     = "restaurant.db"
