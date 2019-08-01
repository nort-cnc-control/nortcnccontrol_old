import socket
import fcntl
import struct

def getHwAddr(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', bytes(ifname, 'utf-8')[:15]))
    return info[18:24]

ifname = 'eno1'

sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.IPPROTO_RAW)
sock.bind((ifname, 0))

dst = bytes([255,255,255,255,255,255])
src = getHwAddr(ifname)
ethertype = bytes([0xFE, 0xFE])
len = bytes([0, 6])
data = b"N0M801"
frame = dst + src + ethertype + len + data

sock.send(frame)
