#!/usr/bin/env python3

import time
import sys
import serial
import event
import asyncio

class SerialSender(object):

    completed = event.EventEmitter()
    queued = event.EventEmitter()

    def __init__(self, port, bdrate):
        self.id = 0
        self.port = port
        self.baudrate = bdrate
        self.ser = serial.Serial(self.port, self.baudrate,
                                 bytesize=8, parity='N', stopbits=1)

    def send_command(self, command):
        cmd = ("N%i" % self.id) + command + "\n"
        self.ser.write(bytes(cmd, "UTF-8"))
        self.ser.flush()
        oid = self.id
        self.id += 1
        return oid

    def close(self):
        self.ser.close()
