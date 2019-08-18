
# If hardware axes is inverted
X_INVERT = False
Y_INVERT = True
Z_INVERT = True

# Left/Right orientation for hardware axes
PLANES_RIGHT = (X_INVERT != Y_INVERT) != Z_INVERT

# size of table
SIZE_X = 224.0
SIZE_Y = 324.0
SIZE_Z = 105.0

# steppers config
FULL_STEPS = 200
MICRO_STEP = 8
MM_PER_ROUND = 4.0

STEPS_PER_MM = (FULL_STEPS * MICRO_STEP) / MM_PER_ROUND

# dynamic properties
ACCELERATION = 40.0
JERKING = 20.0
FASTFEED = 800.0
MAXFEED = 800.0
PRECISE_FEED = 50.0
DEFAULT_FEED = 20.0

# communication settings
TABLE_BAUDRATE = 115200
TABLE_PORT = "eth0"

RS485_BAUDRATE = 9600
RS485_PORT = "/dev/ttyUSB1"

# spindel options
N700E_ID = 1
SPINDLE_MAX = 24000.0
SPINDLE_DELAY = 5.0

# emulation options
EMULATE_TABLE = False
EMULATE_SPINDEL = False

# timeout of request coordinates
COORDINATE_REQUEST_TIMEOUT = 0.1

LISTEN=("0.0.0.0", 10000)
