LOGIN = 0
ADD_MEMBER = 1
BOOKINGS = 2
FLOOR_PLAN = 3
CHOOSE_OPTION = 4
TIME_FORMAT = "%Y-%m-%d %H:%M"

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

DEFAULT_TABLE = {
	"x_pos": 41, # Allows padding for chairs and a 5px margin
	"y_pos": 41,
	"width": 100,
	"height": 100,
	"capacity": 4,
	"table_number": "",
	"shape": 0 # Oval
}

NOT_LOGGED   = "Not logged in"
LOGGED       = "Logged in as {}"
LOGIN_TAG    = "Log In"
LOGOUT_TAG   = "Log Out"
MASK         = "\u2022"
DATABASE     = "restaurant.db"
