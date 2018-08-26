#/usr/bin/env python3

import regex

class GCmd(object):

    def __init__(self, s):
        self.parsed = None
        self.type = s[0]
        self.value = s[1:]
        if "GMT".find(self.type) != -1:
            self.value = int(self.value)
        elif "FXYZABCIJK".find(self.type) != -1:
            self.value = float(self.value)

    def __repr__(self):
        return str(self.type) + str(self.value)

class GFrame(object):

    def __init__(self, cmds, comments):
        self.commands = []
        for cmd in cmds:
            self.commands.append(GCmd(cmd))
        self.comments = comments
    
    def __repr__(self):
        res = str(self.commands[0])
        for cmd in self.commands[1:]:
            res += " " + str(cmd)
        return res

class GLineParser(object):
    def __init__(self):
        pattern = r"(?:%|(?:[ ]*(?:\((.*)\))*[ ]*([A-Z][-|+]?[0-9]*[\.[0-9]*]?))*[ ]*(?:\((.*)\))*[ ]*(?:;(.*))?)"
        self.re = regex.compile(pattern)

    def parse(self, line):
        r = self.re.fullmatch(line)
        if r == None:
            return None

        try:
            frame = GFrame(r.captures(2), r.captures(1) + r.captures(3) + r.captures(4))
            return frame
        except:
            return None
