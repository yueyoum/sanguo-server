# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/11/14'

import random

from mongoengine import DoesNotExist
from mongoscheme import MongoLevy
from core.character import Char
from core.msgpipe import publish_to_char
from core.exception import SanguoException
from core.resource import Resource
from utils import pack_msg
from protomsg import LevyNotify
from preset import errormsg


CRIT_PROB_TABLE = (
    (1, 10),
    (3, 5),
    (8, 3),
    (18, 2),
    (100, 1),
)

class Levy(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.ml = MongoLevy.objects.get(id=self.char_id)
        except DoesNotExist:
            self.ml = MongoLevy(id=self.char_id)
            self.ml.times = 0
            self.ml.save()


    def get_cost_sycee(self):
        if self.ml.times == 0:
            return 0
        if self.ml.times == 1:
            return 10
        if self.ml.times < 6:
            return 20
        if self.ml.times < 20:
            return 40
        return 80

    def max_times(self):
        # TODO VIP
        return 10

    def levy(self):
        max_times = self.max_times()
        if self.ml.times >= max_times:
            raise SanguoException(
                errormsg.LEVY_NO_TIMES,
                self.char_id,
                "Levy levy",
                "no times"
            )

        c = Char(self.char_id)
        resource = Resource(self.char_id, "Levy")

        cost_cyess = self.get_cost_sycee()

        with resource.check(sycee=-cost_cyess):
            got_gold = 10000 * c.mc.level * 2
            prob = random.randint(1, 100)
            for k, v in CRIT_PROB_TABLE:
                if prob <= k:
                    break

            got_gold *= v

            self.ml.times += 1
            self.ml.save()
            resource.add(gold=got_gold)

        self.send_notify()

    def send_notify(self):
        msg = LevyNotify()
        msg.cost_sycee = self.get_cost_sycee()
        publish_to_char(self.char_id, pack_msg(msg))

