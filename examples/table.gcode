G74
G30
G54
G92 Z1.5
G0 Z10
M3 S3000

G0 Y100

M97 P3 L5

M5
M2

N1
G0 Z0
G1 Z-5 F200
G0 Z10

G0 Z0
G1 Z-10 F200
G0 Z10

G0 Z0
G1 Z-15 F200
G0 Z10
M99

N2
M97 P1

G91
G0 X20
G90

M99

N3
M97 P2 L8
M97 P1

G0 X0
G91
G0 Y20
G90
M99
