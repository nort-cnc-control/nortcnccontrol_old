#!/usr/bin/env python3

import serial

import pymodbus

from pymodbus.client.sync import ModbusSerialClient
from pymodbus.pdu import ModbusRequest 
from pymodbus.transaction import ModbusRtuFramer


class Spindel_N700E(object):
    
    __speed_register = 0x0004
    
    __run_register = 0x0002
    __run_forward = 0x0001
    __run_reverse = 0x0002
    __run_stop = 0x0000

    def __init__(self, port, device):
        self.device = device
        self.port = port
        self.baudrate = 9600
        self.client = ModbusSerialClient(method='rtu', port=self.port, stopbits=1, baudrate=self.baudrate, parity='N')
        connected = self.client.connect()
        print("Connected: %s" % str(connected))

    def __write_register(self, register, value):
        self.client.write_register(address=register, value=value, unit=self.device)

    def close(self):
        self.client.close()

    def set_speed(self, speed):
        self.__write_register(self.__speed_register, int(speed / 60.0 * 100))

    def start_forward(self):
        self.__write_register(self.__run_register, self.__run_forward)

    def start_reverse(self):
        self.__write_register(self.__run_register, self.__run_reverse)

    def stop(self):
        self.__write_register(self.__run_register, self.__run_stop)

#client = Spindel_N700E("/dev/ttyUSB1", 1)
#client.set_speed(50)
#client.start_reverse()
#client.stop()
#client.close()

