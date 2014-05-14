# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/6/14'

import random

from mongoengine import DoesNotExist
from core.mongoscheme import MongoCheckIn
from core.msgpipe import publish_to_char
from core.exception import SanguoException
from core.character import Char
from core.counter import Counter
from core.attachment import Attachment, standard_drop_to_attachment_protomsg
from core.achievement import Achievement
from core.resource import Resource
from utils import pack_msg
from protomsg import CheckInNotify, CheckInResponse
from preset.data import GEMS, OFFICIAL
from preset import errormsg

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
            raise SanguoException(
                errormsg.CHECKIN_ALREADY_CHECKIN,
                self.char_id,
                "CheckIn checkin",
                "already checkin",
            )
        self.c.has_checked = True

        self.c.days += 1

        resource_add = {}
        resource_add['sycee'] = 100

        if self.c.days == MAX_DAYS:
            resource_add['stuffs'] = [(22, 5)]

            level_three_gems = []
            for g in GEMS.values():
                if g.level == 3:
                    level_three_gems.append(g.id)

            gid = random.choice(level_three_gems)
            resource_add['gems'] = [(gid, 1)]
            self.c.days = 0

        self.c.save()

        resource = Resource(self.char_id, "Daily Checkin", 'checkin reward')
        standard_drop = resource.add(**resource_add)

        msg = CheckInResponse()
        msg.ret = 0
        msg.reward.MergeFrom(standard_drop_to_attachment_protomsg(standard_drop))

        achievement = Achievement(self.char_id)
        achievement.trig(34, 1)

        return msg


    def daily_reset(self):
        # 每日可签到标志重置
        self.c.has_checked = False
        self.c.save()
        self.send_notify()


    def send_notify(self):
        m = CheckInNotify()
        m.checkin = self.c.has_checked
        m.days = self.c.days
        m.max_days = MAX_DAYS

        publish_to_char(self.char_id, pack_msg(m))


class OfficalDailyReward(object):
    def __init__(self, char_id):
        self.char_id = char_id

    def check(self):
        char = Char(self.char_id)
        official_level = char.cacheobj.official
        if official_level == 0:
            return

        counter = Counter(self.char_id, 'official_reward')
        remained_value = counter.remained_value
        if remained_value > 0:
            attachment = Attachment(self.char_id)
            attachment.save_to_prize(6)


    def get_reward(self):
        counter = Counter(self.char_id, 'official_reward')
        if counter.remained_value <= 0:
            raise SanguoException(
                errormsg.OFFICAL_ALREADY_GET_REWARD,
                self.char_id,
                "OfficalDailyReward Get Reward",
                "already got"
            )


        char = Char(self.char_id)
        official_level = char.mc.official
        if official_level == 0:
            raise SanguoException(
                errormsg.OFFICAL_ZERO_GET_REWARD,
                self.char_id,
                "OfficalDailyReward Get Reward",
                "char official level = 0"
            )

        counter = Counter(self.char_id, 'official_reward')
        counter.incr()

        gold = OFFICIAL[official_level].gold

        resource = Resource(self.char_id, "Daily Official", 'official reward')
        standard_drop = resource.add(gold=gold)
        return standard_drop_to_attachment_protomsg(standard_drop)

