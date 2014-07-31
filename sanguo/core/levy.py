# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/11/14'

import random

from core.character import Char
from core.msgpipe import publish_to_char
from core.exception import SanguoException
from core.resource import Resource
from core.counter import Counter
from utils import pack_msg
from protomsg import LevyNotify
from preset import errormsg
from preset.settings import LEVY_COST_SYCEE, LEVY_CRIT_PROB_TABLE, LEVY_GOT_GOLD_FUNCTION
from preset.data import VIP_MAX_LEVEL

LEVY_COST_SYCEE_REV = list(LEVY_COST_SYCEE)
LEVY_COST_SYCEE_REV.sort(key = lambda item: -item[0])

class Levy(object):
    def __init__(self, char_id):
        self.char_id = char_id
        self.counter = Counter(char_id, 'levy')

    def get_cost_sycee(self):
        for t, s in LEVY_COST_SYCEE_REV:
            if self.counter.cur_value >= t:
                return s

    def get_max_times(self):
        return self.counter.max_value


    def levy(self):
        char = Char(self.char_id).mc

        if self.counter.remained_value <= 0:
            if char.vip < VIP_MAX_LEVEL:
                raise SanguoException(
                    errormsg.LEVY_NO_TIMES,
                    self.char_id,
                    "Levy",
                    "no times. but can get additional times by increase vip level. current: {0}, max: {1}".format(char.vip, VIP_MAX_LEVEL)
                )
            raise SanguoException(
                errormsg.LEVY_NO_TIMES_FINAL,
                self.char_id,
                "Levy",
                "no times. vip reach the max level {0}".format(VIP_MAX_LEVEL)
            )

        resource = Resource(self.char_id, "Levy")
        cost_cyess = self.get_cost_sycee()

        with resource.check(sycee=-cost_cyess):
            got_gold = LEVY_GOT_GOLD_FUNCTION(char.level)
            prob = random.randint(1, 100)
            for k, v in LEVY_CRIT_PROB_TABLE:
                if prob <= k:
                    break

            got_gold *= v

            self.counter.incr()
            resource.add(gold=got_gold)

        self.send_notify()
        return got_gold

    def send_notify(self):
        msg = LevyNotify()
        msg.cost_sycee = self.get_cost_sycee()
        msg.cur_times = self.counter.cur_value
        msg.max_times = self.counter.max_value
        publish_to_char(self.char_id, pack_msg(msg))
