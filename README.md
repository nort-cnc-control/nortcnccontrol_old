# Description

This is a control system for cnc milling machines. It works in conjuction with https://github.com/vladtcvs/cnccontrol_rt,
which performs realtime operations, such as steppers control and end-stops detection.

No realtime kernel is required!

# Supported third-party hardware

- Hyundai N700E vector inverter for spindel

# Components

## Command server

`python3 server/server.py`

Server creates `/tmp/cnccontrol` unix socket, so user should have enougth permissions for this.

### Supported options
- -e - emulate table
- -E - emulate spindel
- -r, --rs485 - port, where spindel inverter connected. default=/dev/ttyUSB1
- -p, --port - port, where board with https://github.com/vladtcvs/cnccontrol_rt connected. default=/dev/ttyUSB0
- -b, --baud - baudrate for board communication. default=9600

### Emulation mode

In this mode no hardware is required, commands to hardware just printed in terminal

## UI

`python3 gui/gcodeconvert.py`, server should be started first

## Launcher

`python3 cnccontrol.py`

Launcher starts command server and ui.

All options from command server are supported

# Supported operations

Cnccontrol supports G-Code commands described in ISO 6983-1:2009,
but only part of commands are implemented.

## Units

All sizes should be specified in millimeters (mm).

## List of supported operations

### G commands

- G00 - fast movement. Moves by line.
- G01 - linear movement with specified
- G02 - clockwise arc movement. Only flat move is now supported.
- G03 - counterclockwise arc movement. Only flat move is now supported.
- G09 - finish current movement with feedrate = 0
- G17 - select XY plane for arc movement
- G18 - select XZ plane for arc movement
- G19 - select YZ plane for arc movement
- G30 - probe Z axis
- G53 - select main coordinate system
- G54-G59 - select one of shifted coordinate systems
- G74 - search Z, X, Y endstops
- G90 - select absolute positioning
- G91 - select relative positioning
- G92 - set current position. One of G54-G59 must be selected.

### M commands

- M00 - pause until 'Continue' pressed
- M02 - program end
- M03 - start spindel clockwise
- M04 - start spindel counterclockwise
- M05 - stop spindel
- M97 - use subprogram
- M99 - return from subprogram
- M120 - push state
- M121 - pop state

### Options

- Sxxx - set spindel rotation speed, rpm
- Txxx - display 'Insert tool' message and wait for continue.
- Fxxx - set feetrate mm/min
- Pxxx - subprogram to call
- Lxxx - amount of calling subprogram

### Coordinates

- X, Y, Z - coordinates of target position
- I, J, K - coordinates of arc center when G02/G03 specified
- R - radius of arc, when G02/G03 specified. R < 0 means make big arc, with angle > 180

## Reseting

CNC milling machine can be stopped in any moment with 'Reset' button in UI. It stops program execution and reboots board.
Note, that coordinates of spindel became invalid after reset, because immediate stop of mill, when it moves with big enougth feedrate can lead to slip. So we can not be sure about real spindel position.

## Coordinate systems

cnccontrol supports one main coordinate system, selected with G53 command, and 6 additional coordinate systems, which are offseted related to main coordinate system.

After searching endstops cutter position in main coordinate system sets to 0, 0, 0. After Z probe, cutter Z position in main coordinate system sets to 0. All offsets of G54-G59 systems are preserved.

# Movement optimizations

cnccoontrol optimizes movements. If we have N movements with same feedrate and direction, cutter won't stop between this movements except G09 is specified. When directions of 2 sequencial movements differs, feedrate is selected so that tangential velocity leap doesn't exceed allowed value.

# Dependencies

python3 and python packages are required:

- wxpython
- serial
- euclid3
- pymodbus

# License

GNU GPLv3+, full text of GNU GPLv3 see in LICENSE file
