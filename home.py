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

sock.send(bytes('{"type" : "command", "command" : "reset"}', "utf-8"))
res = sock.recv(1024)
print(res)

sock.send(bytes('{"type" : "command", "command" : "load", "lines" : ["G28", "M2"]}', "utf-8"))
res = sock.recv(1024)
print(res)
res = sock.recv(1024)
print(res)

sock.send(bytes('{"type" : "command", "command" : "start"}', "utf-8"))
while True:
    res = sock.recv(1024)
    d = json.loads(res)
    if d["type"] == "state" and d["state"] == "completed":
        break

sock.close()

os.remove(tmppath)

