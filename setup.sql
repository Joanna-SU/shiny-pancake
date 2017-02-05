/* Stores the floor plan layout */
CREATE TABLE IF NOT EXISTS layout_table (
	table_id     INTEGER     PRIMARY KEY,
	table_number CHAR(16),
	capacity     INTEGER     NOT NULL,
	x_pos        INTEGER     NOT NULL DEFAULT 0,
	y_pos        INTEGER     NOT NULL DEFAULT 0,
	width        INTEGER     NOT NULL DEFAULT 100,
	height       INTEGER     NOT NULL DEFAULT 100,
	shape        INTEGER     NOT NULL DEFAULT 0
);

/* Stores information about the members of staff */
CREATE TABLE IF NOT EXISTS staff (
	member_id    INTEGER     PRIMARY KEY,
	password     CHAR(32)    NOT NULL,
	salt         CHAR(16)    NOT NULL,
	first_name   VARCHAR(16) NOT NULL,
	last_name    VARCHAR(32) NOT NULL DEFAULT "",
	phone_number CHAR(15)    NOT NULL DEFAULT "",
	present      BOOLEAN     NOT NULL DEFAULT 0,
	permission   BOOLEAN     NOT NULL DEFAULT 0
);

/* Stores all bookings that are coming up */
CREATE TABLE IF NOT EXISTS booking (
	booking_id   INTEGER     PRIMARY KEY,
	member_id    INTEGER,
	table_id     INTEGER     NOT NULL,
	arrival      INTEGER     NOT NULL,
	status       INTEGER     NOT NULL DEFAULT 0,
	ping         BOOLEAN     NOT NULL DEFAULT 0
);
