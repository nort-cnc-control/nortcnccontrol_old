#!/usr/bin/env python3

import os
import socket
import json


path = "/tmp/cnccontrol"

tmppath = path + ".tmp"
if os.path.exists(tmppath):
    os.remove(tmppath)
        
sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

sock.bind(tmppath)
sock.connect(path)

sock.send(bytes('{"type" : "command", "command" : "exit"}', "utf-8"))

res = sock.recv(1024)
print(res)

sock.close()

os.remove(tmppath)

