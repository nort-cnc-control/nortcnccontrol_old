#!/usr/bin/env python3

import optimizer
import euclid3

class FakeMovement(object):
    def __init__(self, d):
        self.delta = euclid3.Vector3(d, 0, 0)
        self.feed = 600
        self.feed0 = 0
        self.feed1 = 0
        self.is_moving = True
        self.exact_stop = False
    def length(self):
        return self.delta.magnitude()
    def dir0(self):
        return self.delta / self.length()
    def dir1(self):
        return self.delta / self.length()

class FakeProgram(object):
    def __init__(self, actions):
        self.actions = actions

acts = []
acts.append((0, FakeMovement(0.1), 0))
acts.append((0, FakeMovement(0.1), 0))
acts.append((0, FakeMovement(0.1), 0))
acts.append((0, FakeMovement(0.1), 0))
acts.append((0, FakeMovement(0.1), 0))
acts.append((0, FakeMovement(0.1), 0))
acts.append((0, FakeMovement(0.1), 0))
acts.append((0, FakeMovement(0.1), 0))
acts.append((0, FakeMovement(0.1), 0))
acts.append((0, FakeMovement(0.1), 0))
acts.append((0, FakeMovement(0.1), 0))
acts.append((0, FakeMovement(0.1), 0))
acts.append((0, FakeMovement(0.1), 0))
acts.append((0, FakeMovement(0.1), 0))


opt = optimizer.Optimizer(20, 20, 600)
opt.optimize(FakeProgram(acts))

for (_, act, _) in acts:
    print(act.feed0, act.feed, act.feed1)
