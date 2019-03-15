#!/usr/bin/env python3

import n700e

client = n700e.Spindel_N700E("/dev/ttyUSB1", 1)
client.set_speed(400*60)
client.start_forward()
client.close()

