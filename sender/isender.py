#!/usr/bin/env python3
import abc

class ISender(object):

    @abc.abstractmethod
    def send_command(self, comamnd):
        pass
