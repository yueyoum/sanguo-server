# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-12-10'

import arrow

from mongoengine import DoesNotExist
from core.mongoscheme import MongoUnionMember, MongoUnion

from core.exception import SanguoException
from core.vip import VIP
from core.resource import Resource
from core.msgfactory import create_character_infomation_message
from core.msgpipe import publish_to_char

from utils import pack_msg

from preset import errormsg
from preset.data import (
    UNION_CHECKIN,
    UNION_POSITION,

)


import protomsg

MAX_UNION_POSITION = max(UNION_POSITION.keys())

class Member(object):
    """
    一个工会成员对象
    成员相关操作
    """
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.mongo_union_member = MongoUnionMember.objects.get(id=char_id)
        except DoesNotExist:
            self.mongo_union_member = MongoUnionMember(id=char_id)
            self.mongo_union_member.buy_buff_times = {}
            self.mongo_union_member.save()

    @property
    def checkin_total_amount(self):
        return VIP(self.char_id).get_max_times('union_checkin')

    @property
    def checkin_current_amount(self):
        return self.mongo_union_member.checkin_times

    def checkin(self):
        # 签到
        from core.union.union import Union

        if not self.mongo_union_member.joined:
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                self.char_id,
                "Union Checkin",
                "not join union"
            )

        if self.mongo_union_member.checkin_times + 1 > self.checkin_total_amount:
            raise SanguoException(
                errormsg.UNION_CHECKIN_REACH_MAX_TIMES,
                self.char_id,
                "Union Checkin",
                "reached max times"
            )

        try:
            c = UNION_CHECKIN[self.mongo_union_member.checkin_times+1]
        except KeyError:
            raise SanguoException(
                errormsg.UNION_CHECKIN_REACH_MAX_TIMES,
                self.char_id,
                "Union Checkin",
                "reached max times. UNION_CHECKIN KeyError: {0}".format(self.mongo_union_member.checkin_times+1)
            )

        if c.cost_type == 1:
            needs = {'gold': -c.cost_value}
        else:
            needs = {'sycee': -c.cost_value}

        resources = Resource(self.char_id, "Union Checkin")
        with resources.check(**needs):
            self.mongo_union_member.checkin_times += 1
            self.mongo_union_member.last_checkin_timestamp = arrow.utcnow().timestamp

            self.add_coin(c.got_coin, send_notify=False)
            self.add_contribute_points(c.got_contributes, send_notify=False)
            self.mongo_union_member.save()
        self.send_personal_notify()


        Union(self.char_id).add_contribute_points(c.got_contributes)


    def make_member_message(self):
        msg = protomsg.UnionNotify.UnionMember()
        msg.char.MergeFrom(create_character_infomation_message(self.char_id))
        msg.position = self.mongo_union_member.position
        msg.contribute_points = self.mongo_union_member.contribute_points
        return msg

    def send_personal_notify(self):
        if not self.mongo_union_member.joined:
            return

        msg = protomsg.UnionPersonalInformationNotify()
        msg.union_coin = self.mongo_union_member.coin

        msg.checkin_total_amount = self.checkin_total_amount
        msg.checkin_current_amount = self.checkin_current_amount

        publish_to_char(self.char_id, pack_msg(msg))


    def apply_union(self, union_id):
        # 申请加入工会
        from core.union.union import Union, UnionList

        try:
            mongo_union = MongoUnion.objects.get(id=union_id)
        except DoesNotExist:
            raise SanguoException(
                errormsg.UNION_NOT_EXIST,
                self.char_id,
                "Member Apply Union",
                "union {0} not exist".format(union_id)
            )

        if self.mongo_union_member.joined:
            raise SanguoException(
                errormsg.UNION_CANNOT_APPLY_ALREADY_IN,
                self.char_id,
                "Member Apply Union",
                "already in {0}".format(self.mongo_union_member.joined)
            )

        if len(self.mongo_union_member.applied) >= 10:
            raise SanguoException(
                errormsg.UNION_CANNOT_APPLY_FULL,
                self.char_id,
                "Member Apply Union",
                "apply list too long"
            )


        if union_id not in self.mongo_union_member.applied:
            self.mongo_union_member.applied.append(union_id)
            self.mongo_union_member.save()

            Union(mongo_union.owner).send_apply_list_notify()


        UnionList.send_list_notify(self.char_id)


    def join_union(self, union_id):
        # 加入工会 - 由Union调用
        try:
            MongoUnion.objects.get(id=union_id)
        except DoesNotExist:
            raise SanguoException(
                    errormsg.UNION_NOT_EXIST,
                    self.char_id,
                    "UnionMember Join Union",
                    "union {0} not eixst".format(union_id)
                    )

        if self.mongo_union_member.joined == union_id:
            return

        self.mongo_union_member.applied = []
        self.mongo_union_member.joined = union_id
        self.mongo_union_member.contribute_points = 0
        self.mongo_union_member.position = 1
        self.mongo_union_member.last_checkin_timestamp = 0
        self.mongo_union_member.save()
        self.send_personal_notify()

    def quit_union(self):
        # 退出工会 - 由Union调用
        self.mongo_union_member.joined = 0
        self.mongo_union_member.contribute_points = 0
        self.mongo_union_member.position = 1
        self.mongo_union_member.last_checkin_timestamp = 0
        self.mongo_union_member.save()
        self.send_personal_notify()


    def check_coin(self, coin_needs, raise_exception=False, func_name=""):
        if not raise_exception:
            if self.mongo_union_member.coin < coin_needs:
                return False
            return True

        if self.mongo_union_member.coin < coin_needs:
            raise SanguoException(
                errormsg.UNION_COIN_NOT_ENOUGH,
                self.char_id,
                func_name,
                "union coin not enough, {0} < {1}".format(self.mongo_union_member.coin, coin_needs)
            )

    def cost_coin(self, coin_needs):
        self.mongo_union_member.coin -= coin_needs
        self.mongo_union_member.save()
        self.send_personal_notify()

    def add_coin(self, coin, send_notify=True):
        self.mongo_union_member.coin += coin
        self.mongo_union_member.save()
        if send_notify:
            self.send_personal_notify()

    def add_contribute_points(self, point, send_notify=True):
        self.mongo_union_member.contribute_points += point
        to_next_position_contributes_needs = UNION_POSITION[self.mongo_union_member.position].contributes_needs

        if self.mongo_union_member.position >= MAX_UNION_POSITION:
            self.mongo_union_member.position = MAX_UNION_POSITION
            if self.mongo_union_member.contribute_points >= to_next_position_contributes_needs:
                self.mongo_union_member.contribute_points = to_next_position_contributes_needs
        else:
            if self.mongo_union_member.contribute_points >= to_next_position_contributes_needs:
                self.mongo_union_member.contribute_points -= to_next_position_contributes_needs
                self.mongo_union_member.position += 1

        self.mongo_union_member.save()
        if send_notify:
            self.send_personal_notify()


    def cron_job(self):
        self.mongo_union_member.checkin_times = 0
        self.mongo_union_member.boss_times = 0
        self.mongo_union_member.save()
        self.send_personal_notify()





