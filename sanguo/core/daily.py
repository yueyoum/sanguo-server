# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/6/14'

import datetime

from mongoengine import DoesNotExist
from core.mongoscheme import MongoCheckIn
from utils import pack_msg
from core.msgpipe import publish_to_char
from core.exception import InvalidOperate

from protomsg import CheckInNotify


# FIXME
TP = [2, 5, 10, 17, 26]


class CheckIn(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.c = MongoCheckIn.objects.get(id=char_id)
        except DoesNotExist:
            self.c = MongoCheckIn(id=char_id)
            self.c.save()

    @property
    def checkin_days(self):
        return self.c.days

    @property
    def whole_days(self):
        return len(self.c.days)

    def checkin(self):
        day = datetime.datetime.now().day
        if day not in self.c.days:
            self.c.days.append(day)
            self.c.save()

        self.send_notify()

    def get_reward(self, tp):
        if tp not in TP:
            raise InvalidOperate()

        if tp in self.c.has_get:
            raise InvalidOperate()

        # TODO send reward

        self.c.has_get.append(tp)
        self.c.save()
        self.send_notify()



    def send_notify(self):
        has_get = self.c.has_get

        m = CheckInNotify()
        m.checkin_days.extend(self.checkin_days)
        for tp in TP:
            t = m.tp.add()
            t.tp = tp
            t.complete = m.checkin_days >= tp
            t.finished = tp in has_get

        publish_to_char(self.char_id, pack_msg(m))