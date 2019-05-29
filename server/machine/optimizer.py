import euclid3
import math

class Optimizer(object):

    def __init__(self, max_jerk, max_acc, max_feed):
        self.max_acc = max_acc
        self.max_jerk = max_jerk / 60.0
        self.max_feed = max_feed / 60.0

    @staticmethod
    def __sc(a, b):
        return a.x * b.x + a.y * b.y + a.z * b.z

    def __fill_max_feed(self, actions):
        # set maximal feed for each action
        for action, _ in actions:
            action.max_feed = min(self.max_feed, action.feed / 60.0)
            # set maximal feed for arcs
            try:
                r = action.r
                maxf = (r * self.max_acc)**0.5
                action.max_feed = min(maxf, action.max_feed)
            except:
                pass

    def __max_feed_jerk(self, dir1, dir2):
        cosa = self.__sc(dir1, dir2)
        if cosa > 1:
            cosa = 1
        if cosa <= 1e-4:
            return 0
        else:
            sina = (1-cosa**2)**0.5
            if sina > 1e-4:
                maxf2 = self.max_jerk / sina
                maxf1 = self.max_jerk / (1 - cosa)
            else:
                maxf1 = self.max_feed
                maxf2 = self.max_feed
            return min(maxf1, maxf2)

    def __fill_max_feed_01(self, actions):
        # set maximal feed0 and feed1
        for i in range(len(actions)):
            action = actions[i][0]

            dir0 = actions[i][1]["dir0"]
            if i > 0:
                prevdir = actions[i-1][1]["dir1"]
                prevmf = actions[i-1][0].max_feed
            else:
                prevdir = euclid3.Vector3(0,0,0)
                prevmf = 0

            action.max_feed0 = min([self.__max_feed_jerk(prevdir, dir0), action.max_feed, prevmf])

            dir1 = actions[i][1]["dir1"]
            if i < len(actions)-1:
                nextdir = actions[i+1][1]["dir0"]
                nextmf = actions[i+1][0].max_feed
            else:
                nextdir = euclid3.Vector3(0,0,0)
                nextmf = 0
            action.max_feed1 = min([self.__max_feed_jerk(nextdir, dir1), action.max_feed, nextmf])

    def __pos_feed(self, x0, f0, x1, f1):
        x = (x0 + x1) / 2 + (f1**2 - f0**2) / (4*self.max_acc)
        f = ((f0**2 + f1**2)/2 + self.max_acc * (x1 - x0))**0.5
        return x, f

    def __feed0(self, f, x, x0):
        f02 = max(f**2 - 2*self.max_acc * (x - x0), 0)
        return f02**0.5

    def __feed1(self, f, x, x1):
        f12 = max(f**2 - 2*self.max_acc * (x1 - x), 0)
        return f12**0.5

    def __feeds(self, limits, index):
        xm = None
        fm = None
        f0m = limits[index][1]
        f1m = limits[index+1][1]
        assert(index < len(limits) - 1)
        xbegin = limits[index][0]
        xend = limits[index+1][0]
        for i in range(index+1):
            x0 = limits[i][0]
            f0 = limits[i][1]
            for j in range(index+1, len(limits)):
                x1 = limits[j][0]
                f1 = limits[j][1]
                x,f = self.__pos_feed(x0, f0, x1, f1)
                if fm is None or fm > f:
                    xm = x
                    fm = f
        if xm >= xbegin and xm <= xend:
            f0 = min(self.__feed0(fm, xm, xbegin), f0m)
            f1 = min(self.__feed1(fm, xm, xend), f1m)
            return f0, fm, f1
        elif xm > xend:
            f0 = min(self.__feed0(fm, xm, xbegin), f0m)
            f1 = min(self.__feed0(fm, xm, xend), f1m)
            return f0, f1, f1
        elif xm < xbegin:
            f0 = min(self.__feed1(fm, xm, xbegin), f0m)
            f1 = min(self.__feed1(fm, xm, xend), f1m)
            return f0, f0, f1    
    
    def __process_chain(self, actions):
        if len(actions) == 0:
            return
        limits = [(0, actions[0][0].max_feed0)]
        x = 0
        for action, _ in actions:
            x += action.length()
            limits.append((x, action.max_feed1))

        for i in range(len(limits) - 1):
            f0, f, f1 = self.__feeds(limits, i)
            actions[i][0].feed0 = f0*60
            actions[i][0].feed = min(f, actions[i][0].max_feed)*60
            actions[i][0].feed1 = f1*60
            if actions[i][0].feed < 1:
                print("Zero feed: ", actions[i][0])
                print("f = ", f)
                print("max_feed = ", actions[i][0].max_feed)
                print("length = ", actions[i][0].length())
    # optimize chain
    def __optimize_chain(self, actions):
        self.__fill_max_feed(actions)
        self.__fill_max_feed_01(actions)
        self.__process_chain(actions)

    # optimize program
    #
    # divide it to chains
    # and optimize each chain
    def optimize(self, program):
        chain = []
        print("Start optimization")
        for (_, action, _, extra) in program.actions:
            if action.is_moving == False or extra is None:
                if len(chain) > 0:
                    self.__optimize_chain(chain)
                    chain = []
                continue

            chain.append((action, extra))
            if action.exact_stop == True:
                self.__optimize_chain(chain)
                chain = []

        if len(chain) > 0:
            self.__optimize_chain(chain)
        print("Optimized")
