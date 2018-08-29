#!/usr/bin/env python3

import time
import sys
import serial

class SerialSender(object):

    def __init__(self, port, bdrate):
        self.port = port
        self.baudrate = bdrate
        self.ser = serial.Serial(self.port, self.baudrate,
                                 bytesize=8, parity='N', stopbits=1,
                                 timeout=1)

    def queue_command(self, command):
        cmd = command + "\n"
        self.ser.write(bytes(cmd, "UTF-8"))
        self.ser.flush()
        has_answer = False
        while not has_answer:
            ans = self.ser.readline()
            print("Ans: %s" % ans)
            has_answer = True

    def close(self):
        self.ser.close()
