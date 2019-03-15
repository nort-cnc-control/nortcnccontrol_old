#!/usr/bin/env python3

import n700e

client = n700e.Spindel_N700E("/dev/ttyUSB1", 1)
client.stop()
client.close()

