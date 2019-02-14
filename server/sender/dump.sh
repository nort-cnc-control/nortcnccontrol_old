socat /dev/ttyUSB0,raw,echo=0 SYSTEM:'tee in.txt |socat - "PTY,link=rs485,raw,echo=0,waitslave" |tee out.txt'
