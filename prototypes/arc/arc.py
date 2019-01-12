#!/usr/bin/env python3

import math

s = 500
a = 400 * s
b = 400 * s

gx = 0
gy = 0

def step_x(dir):
    global gx, gy
    if dir > 0:
        #print("X++")
        gx += 1
    else:
        gx -= 1
        #print("X--")

def step_y(dir):
    global gx, gy
    if dir > 0:
        #print("Y++")
        gy += 1
    else:
        gy -= 1
        #print("Y--")

def fun(x, a, b):
    return b * math.sqrt(1 - (x**2)/(a**2))

def ifun(x, a, b):
    return int(fun(x, a, b) + 0.5)

def maxx(a, b):
    return a**2 / math.sqrt(a**2 + b**2)

def imaxx(a, b):
    return int(maxx(a, b) + 0.5)

def do_arc_axis(x0, x1, a, b, sign, stx, sty):
    global gx, gy
    if x1 > x0:
        dx = 1
    else:
        dx = -1
    x = x0
    y = ifun(x0, a, b) * sign
    while x != x1:
        x += dx
        stx(dx)
        yx = fun(x, a, b) * sign
        if abs((y - 1)**2 - yx**2) < abs(y**2 - yx**2):
            y -= 1
            sty(-1)
        elif abs((y + 1)**2 - yx**2) < abs(y**2 - yx**2):
            y += 1
            sty(1)
        print(gx, gy)
        
class ArcSegment(object):
    def __init__(self, x0, y0, x1, y1, a, b):
        self.start = (x0, y0)
        self.finish = (x1, y1)
        self.a = a
        self.b = b
        x_s = imaxx(a, b)
        y_s = ifun(x_s, a, b)
        self.go_y = False
        self.go_x = False
        self.sign = None
        if x0 <= -x_s and x1 <= -x_s:
            self.go_y = True
            self.sign = -1
        elif x0 >= x_s and x1 >= x_s:
            self.go_y = True
            self.sign = 1
        elif y0 >= y_s and y1 >= y_s:
            self.go_x = True
            self.sign = 1
        elif y0 <= -y_s and y1 <= -y_s:
            self.go_x = True
            self.sign = -1
        else:
            raise Exception("Bad arguments")

    def reverse(self):
        t = self.start
        self.start = self.finish
        self.finish = t

    def __do_arc_x(self, x0, x1, a, b, sign):
        do_arc_axis(x0, x1, a, b, sign, step_x, step_y)

    def __do_arc_y(self, y0, y1, a, b, sign):
        do_arc_axis(y0, y1, b, a, sign, step_y, step_x)

    def do_arc(self):
        #print(self.start, self.finish)
        if self.go_x:
            self.__do_arc_x(self.start[0], self.finish[0], self.a, self.b, self.sign)
        elif self.go_y:
            self.__do_arc_y(self.start[1], self.finish[1], self.a, self.b, self.sign)

def arc_bottom_ccw(x_s, y_s, x1, y1, arcs):
    if y1 <= -y_s:
        arcs.append(ArcSegment(-x_s, -y_s, x1, y1, a, b))
        return True
    else:
        arcs.append(ArcSegment(-x_s, -y_s, x_s, -y_s, a, b))
        return False

def arc_right_ccw(x_s, y_s, x1, y1, arcs):
    if x1 >= x_s: 
        arcs.append(ArcSegment(x_s, -y_s, x1, y1, a, b))
        return True
    else:
        arcs.append(ArcSegment(x_s, -y_s, x_s, y_s, a, b))
        return False

def arc_left_ccw(x_s, y_s, x1, y1, arcs):
    if x1 <= -x_s:
        arcs.append(ArcSegment(-x_s, y_s, x1, y1, a, b))
        return True
    else:
        arcs.append(ArcSegment(-x_s, y_s, -x_s, -y_s, a, b))
        return False

def arc_top_ccw(x_s, y_s, x1, y1, arcs):
    if y1 >= y_s: 
        arcs.append(ArcSegment(x_s, y_s, x1, y1, a, b))
        return True
    else:
        arcs.append(ArcSegment(x_s, y_s, -x_s, y_s, a, b))
        return False

def make_arcs_ccw(begin, end, a, b):
    x_s = imaxx(a, b)
    y_s = ifun(x_s, a, b)
    points = [(x_s, y_s), (-x_s, y_s), (-x_s, -y_s), (x_s, -y_s)]
    x0 = begin[0]
    y0 = begin[1]
    x1 = end[0]
    y1 = end[1]
    #print(x_s, y_s)
    if x0 >= x_s:
        arcs = []
        if x1 >= x_s and y1 >= y0:
            arcs.append(ArcSegment(x0, y0, x1, y1, a, b))
            return arcs
        else:
            arcs.append(ArcSegment(x0, y0, x_s, y_s, a, b))

        if arc_top_ccw(x_s, y_s, x1, y1, arcs):
            return arcs
        
        if arc_left_ccw(x_s, y_s, x1, y1, arcs):
            return arcs

        if arc_bottom_ccw(x_s, y_s, x1, y1, arcs):
            return arcs

        arcs.append(ArcSegment(x_s, -y_s, x1, y1, a, b))
        return arcs

    elif x0 <= -x_s:
        arcs = []
        if x1 <= -x_s and y1 <= y0: 
            arcs.append(ArcSegment(x0, y0, x1, y1, a, b))
            return arcs
        else:
            arcs.append(ArcSegment(x0, y0, -x_s, -y_s, a, b))

        if arc_bottom_ccw(x_s, y_s, x1, y1, arcs):
            return arcs

        if arc_right_ccw(x_s, y_s, x1, y1, arcs):
            return arcs

        if arc_top_ccw(x_s, y_s, x1, y1, arcs):
            return arcs

        arcs.append(ArcSegment(-x_s, y_s, x1, y1, a, b))
        return arcs

    elif y0 >= y_s:
        arcs = []
        if y1 >= y_s and x1 <= x0:        
            arcs.append(ArcSegment(x0, y0, x1, y1, a, b))
            return arcs
        else:
            arcs.append(ArcSegment(x0, y0, -x_s, y_s, a, b))

        if arc_left_ccw(x_s, y_s, x1, y1, arcs):
            return arcs
        
        if arc_bottom_ccw(x_s, y_s, x1, y1, arcs):
            return arcs

        if arc_right_ccw(x_s, y_s, x1, y1, arcs):
            return arcs

        arcs.append(ArcSegment(x_s, y_s, x1, y1, a, b))
        return arcs
    else:
        arcs = []
        if y1 <= -y_s and x1 > x0:        
            arcs.append(ArcSegment(x0, y0, x1, y1, a, b))
            return arcs
        else:
            arcs.append(ArcSegment(x0, y0, x_s, -y_s, a, b))

        if arc_right_ccw(x_s, y_s, x1, y1, arcs):
            return arcs

        if arc_top_ccw(x_s, y_s, x1, y1, arcs):
            return arcs

        if arc_left_ccw(x_s, y_s, x1, y1, arcs):
            return arcs

        arcs.append(ArcSegment(-x_s, -y_s, x1, y1, a, b))
        return arcs

def make_arcs_cw(begin, end, a, b):
    res = []
    arcs = make_arcs_ccw(end, begin, a, b)
    l = len(arcs)
    for i in range(len(arcs)):
        a = arcs[l - i - 1]
        a.reverse()
        res.append(a)
    return res

def do_arc(p0, p1, a, b, cw):
    if cw:
        arcs = make_arcs_cw(p0, p1, a, b)
    else:
        arcs = make_arcs_ccw(p0, p1, a, b)
   
    for arc in arcs:
        arc.do_arc()
        print("finish segment")

x_s = imaxx(a, b)
y_s = ifun(x_s, a, b)

gx = 0
gy = 0
do_arc((-a, 0), (a, 0), a, b, True)

