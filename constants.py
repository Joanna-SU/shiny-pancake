from tkinter import RAISED, SUNKEN, DISABLED, NORMAL, \
	E, W, EW, N, S, NS, NSEW, VERTICAL, CENTER, RIGHT, END

TIME_FORMAT = "%Y-%m-%d %H:%M"

# Indices for main window frames
LOGIN         = 0
ADD_MEMBER    = 1
BOOKINGS      = 2
FLOOR_PLAN    = 3
CHOOSE_OPTION = 4
BUTTONS = ["Log In", "Member Manager", "Booking Manager", "Floor Plan Manager"]

NOT_LOGGED   = "Not logged in"
LOGGED       = "Logged in as {}"
LOGIN_TAG    = "Log In"
LOGOUT_TAG   = "Log Out"

# Fields on the member form
FIELDS = (
	("member_id", "ID"),
	("first_name", "First Name"),
	("last_name", "Last Name"),
	("phone_number", "Phone Number"),
	("password", "Password")
)
# Fields on the table details form
TABLE_FIELDS = (
	("table_number", "Table Number"),
	("capacity", "Capacity"),
	("x_pos", "X Position"),
	("y_pos", "Y Position"),
	("width", "Width"),
	("height", "Height")
)

MASK     = "\u2022" # U+2022 BULLET
DATABASE = "restaurant.db"

STATUSES = (
	"Empty",
	"Arrived",
	"Ordered",
	"Eating",
	"Ready for bill",
	"Completed"
)
# In seconds, estimate times between each status
STATUS_TIMES = (
	-1,
	600,
	900,
	2400,
	300
)

EMPTY     = 0
ARRIVED   = 1
ORDERED   = 2
EATING    = 3
PAYING    = 4
COMPLETED = 5

# Colors to display on the floor plan
TABLE_COLORS = (
	"#97b9ef",
	"#d671f2",
	"#f2775c",
	"#b0ef86",
	"#fccd5f",
	"#6186ed"
)
