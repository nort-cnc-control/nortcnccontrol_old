This is a control system for my cnc. It works in conjuction with https://github.com/vladtcvs/cnccontrol_rt,
which performs realtime operations, such as steppers control and end-stops detection.

This repository contains several components:

* UI
* G-Code parser
* G-Code processor, which builds commands for cnc realtime board
* Interface for realtime operations board
* Interface for spindel frequency changer.

Running in emulation mode

$ ./cnccontrol.py -e

In this case commands for realtime operations board and frequency changer will be printed in terminal
