# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/6/14'

import random

from mongoengine import DoesNotExist
from core.mongoscheme import MongoCheckIn
from utils import pack_msg
from core.msgpipe import publish_to_char
from core.exception import InvalidOperate
from core.character import Char
from core.item import Item
from apps.item.models import Gem as ModelGem
from protomsg import CheckInNotify, CheckInResponse


MAX_DAYS = 7


class CheckIn(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.c = MongoCheckIn.objects.get(id=char_id)
        except DoesNotExist:
            self.c = MongoCheckIn(id=char_id)
            self.c.has_checked = False
            self.c.days = 0
            self.c.save()


    def checkin(self):
        if self.c.has_checked:
            raise InvalidOperate("CheckIN: Char {0} Try to checkin, But already checked".format(self.char_id))
        self.c.has_checked = True

        self.c.days += 1

        msg = CheckInResponse()
        msg.ret = 0
        if self.c.days == MAX_DAYS:
            msg.reward.sycee = 100
            stuff = msg.reward.stuffs.add()
            stuff.id = 22
            stuff.amount = 5

            all_gems = ModelGem.all()
            level_three_gems = []
            for g in all_gems.values():
                if g.level == 3:
                    level_three_gems.append(g.id)

            gid = random.choice(level_three_gems)
            gem = msg.reward.gems.add()
            gem.id = gid
            gem.amount = 1

            char = Char(self.char_id)
            char.update(sycee=100)

            item = Item(self.char_id)
            item.stuff_add((22, 5))
            item.gem_add((gid, 1))

            self.c.days = 0
        else:
            msg.reward.sycee = 100
            char = Char(self.char_id)
            char.update(sycee=100)

        self.c.save()
        return msg


    def daily_reset(self):
        # 每日可签到标志重置
        self.c.has_checked = False
        self.c.save()
        self.send_notify()


    def send_notify(self):
        m = CheckInNotify()
        m.checkin = not self.c.has_checked
        m.days = self.c.days
        m.max_days = MAX_DAYS

        publish_to_char(self.char_id, pack_msg(m))
