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
from core.attachment import Attachment, standard_drop_to_attachment_protomsg, get_drop_from_raw_package
from core.achievement import Achievement
from core.resource import Resource
from utils import pack_msg
from utils.api import api_get_checkin_data

from protomsg import CheckInNotify, CheckInResponse, CheckInUpdateNotify, CheckInItem
from preset.data import GEMS, OFFICIAL
from preset import errormsg

MAX_DAYS = 7


CHECKIN_DATA = {}
# {
#   index_number: {
#     'icons': [(icon_one_type, icon_one_id, icon_one_amount), ...],
#     'package': package
#   },
#   ...
# }

def get_checkin_data():
    global CHECKIN_DATA
    res = api_get_checkin_data(data={})
    CHECKIN_DATA = res['data']['checkin']

get_checkin_data()


def receive_checkin_data(data):
    global CHECKIN_DATA
    CHECKIN_DATA = data



class CheckIn(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.c = MongoCheckIn.objects.get(id=char_id)
        except DoesNotExist:
            self.c = MongoCheckIn(id=char_id)
            self.c.has_checked = False
            self.c.day = 1
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
        day = self.c.day

        self.c.save()

        resource = Resource(self.char_id, "Daily Checkin", 'checkin reward. day {0}'.format(day))
        resource_add = CHECKIN_DATA[str(day)]['package']
        resource_add = get_drop_from_raw_package(resource_add)

        standard_drop = resource.add(**resource_add)

        msg = CheckInResponse()
        msg.ret = 0
        msg.reward.MergeFrom(standard_drop_to_attachment_protomsg(standard_drop))

        self.send_update_notify(day)
        return msg


    def daily_reset(self):
        # 每日可签到标志重置
        self.c.has_checked = False

        if self.c.day == MAX_DAYS:
            self.c.day = 1
        else:
            self.c.day += 1

        self.c.save()
        self.send_notify()


    def _fill_up_one_item(self, item, k):
        k = int(k)
        item.id = k
        if k < self.c.day:
            status = CheckInItem.SIGNED
        elif k == self.c.day:
            if self.c.has_checked:
                status = CheckInItem.SIGNED
            else:
                status = CheckInItem.SIGNABLE
        else:
            status = CheckInItem.UNSIGNED

        item.status = status

        for _tp, _id, _amount in CHECKIN_DATA[str(k)]['icons']:
            obj = item.objs.add()
            obj.tp, obj.id, obj.amount = _tp, _id, _amount


    def send_update_notify(self, k):
        msg = CheckInUpdateNotify()
        self._fill_up_one_item(msg.item, k)
        publish_to_char(self.char_id, pack_msg(msg))


    def send_notify(self):
        msg = CheckInNotify()
        for k in CHECKIN_DATA.keys():
            item = msg.items.add()
            self._fill_up_one_item(item, k)

        publish_to_char(self.char_id, pack_msg(msg))


class OfficialDailyReward(object):
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
                "OfficialDailyReward Get Reward",
                "already got"
            )


        char = Char(self.char_id)
        official_level = char.mc.official
        if official_level == 0:
            raise SanguoException(
                errormsg.OFFICAL_ZERO_GET_REWARD,
                self.char_id,
                "OfficialDailyReward Get Reward",
                "char official level = 0"
            )

        counter = Counter(self.char_id, 'official_reward')
        counter.incr()

        gold = OFFICIAL[official_level].gold

        resource = Resource(self.char_id, "Daily Official", 'official reward')
        standard_drop = resource.add(gold=gold)
        return standard_drop_to_attachment_protomsg(standard_drop)

