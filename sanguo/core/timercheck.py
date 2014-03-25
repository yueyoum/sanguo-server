# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/26/14'

from utils.timezone import utc_timestamp

CHECK_INTERVAL = 120

class TimerCheckAbstractBase(object):
    def check(self):
        raise NotImplementedError()



class TimerCheck(object):
    def __init__(self):
        self.checkers = []
        self.check_time = {}

    def register(self, CheckClass):
        """

        @param CheckClass:
        @type CheckClass: TimerCheckAbstractBase
        """

        if CheckClass not in self.checkers:
            self.checkers.append(CheckClass)


    def check(self, char_id):
        now = utc_timestamp()
        # XXX
        # if char_id in self.check_time and now - self.check_time[char_id] < CHECK_INTERVAL:
        #     return

        self.check_time[char_id] = now
        for cls in self.checkers:
            ck = cls(char_id)
            ck.check()


timercheck = TimerCheck()
