#/usr/bin/env python3

class GCmd(object):

    def __init__(self, s):
        self.parsed = None
        self.type = s[0]
        self.value = s[1:]
        if "GMTPL".find(self.type) != -1:
            self.value = int(self.value)
        elif "FXYZABCIJKSR".find(self.type) != -1:
            self.value = float(self.value)

    def __repr__(self):
        return str(self.type) + str(self.value)

class GFrame(object):

    def __init__(self, commands=[]):
        self.commands = commands
        self.comments = []
    
    def add_cmd(self, cmd):
        self.commands.append(cmd)
    
    def add_comment(self, comment):
        self.comments.append(comment)

    def __repr__(self):
        if len(self.commands) == 0:
            return ""
        res = str(self.commands[0])
        for cmd in self.commands[1:]:
            res += " " + str(cmd)
        return res

class GLineParser(object):

    def __omit_space(self, s):
        while len(s) > 0 and s[0] == " ":
            s = s[1:]
        return s
    
    def __parse_comment_bracket(self, s):
        if len(s) == 0 or s[0] != '(':
            raise Exception("Invalid call of parse comment")
        s = s[1:]
        pos = s.find(')')
        if pos == -1:
            return None, s
        c = s[:pos]
        s = s[pos + 1:]
        return s, c

    def __parse_comment_semicolon(self, s):
        if len(s) == 0 or s[0] != ';':
            raise Exception("Invalid call of parse comment")
        s = s[1:]
        return None, s

    def __parse_word(self, s):
        if len(s) == 0:
            raise Exception("Invalid call of parse word")
        if not (s[0].isalpha() and s[0].isupper()):
            raise Exception("Invalid call of parse word %s" % s)
        cmd = s[0]
        s = s[1:]
        n = s
        while len(s) > 0 and "0123456789.+-[]#=".find(s[0]) != -1:
            s = s[1:]

        if len(s) > 0:
            pos = n.find(s)
            n = n[:pos]
        gc = GCmd(cmd + n)
        return s, gc

    def __parse_frame(self, s):
        frame = GFrame([])
        while s != None and len(s) > 0:
            if s[0] == "\n":
                break
            elif s[0] == " ":
                s = self.__omit_space(s)
            elif s[0] == "(":
                s, comment = self.__parse_comment_bracket(s)
                frame.add_comment(comment)
            elif s[0] == ";":
                s, comment = self.__parse_comment_semicolon(s)
                frame.add_comment(comment)
            else:
                s, cmd = self.__parse_word(s)
                frame.add_cmd(cmd)
        return frame

    def parse(self, line):
        line = self.__omit_space(line)
        if len(line) == 0:
            return GFrame()
        elif line[0] == "%":
            return GFrame()
        return self.__parse_frame(line)

