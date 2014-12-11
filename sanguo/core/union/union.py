# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-12-10'

"""
工会自身
"""

import arrow
from mongoengine import DoesNotExist
from core.mongoscheme import MongoUnion, MongoUnionMember

from core.exception import SanguoException
from core.msgpipe import publish_to_char

from core.msgfactory import create_character_infomation_message

from utils import pack_msg

from preset import errormsg
from preset.data import (
    UNION_LEVEL,
)

import protomsg

MAX_UNION_LEVEL = max(UNION_LEVEL.keys())


class Union(object):
    def __new__(cls, char_id, union_id=None):
        if not union_id:
            try:
                union_id = MongoUnionMember.objects.get(id=char_id).joined
            except DoesNotExist:
                return UnionDummy(char_id)
            if not union_id:
                return UnionDummy(char_id)

        mongo_union = MongoUnion.objects.get(id=union_id)
        belong_to_self = char_id == mongo_union.owner
        if belong_to_self:
            return UnionOwner(char_id, union_id, mongo_union)
        return UnionMember(char_id, union_id, mongo_union)



class UnionBase(object):
    def __init__(self, char_id, union_id, mongo_union):
        self.char_id = char_id
        self.union_id = union_id
        self.mongo_union = MongoUnion.objects.get(id=union_id)

    @property
    def applied_list(self):
        # 申请者ID列表
        mongo_members = MongoUnionMember.objects.filter(applied=self.union_id)
        return [i.id for i in mongo_members]

    @property
    def member_list(self):
        # 成员ID列表
        members = MongoUnionMember.objects.filter(joined=self.union_id)
        return [i.id for i in members]

    @property
    def max_member_amount(self):
        return UNION_LEVEL[self.mongo_union.level].member_limits

    @property
    def current_member_amount(self):
        return MongoUnionMember.objects.filter(joined=self.union_id).count()

    def is_applied(self, char_id):
        # 角色char_id是否申请过
        return char_id in self.applied_list

    def quit(self):
        # 主动退出
        from core.union.member import Member
        Member(self.char_id).quit_union()


    def make_basic_information(self):
        from core.union.battle import UnionBattle
        msg = protomsg.UnionBasicInformation()
        msg.id = self.mongo_union.id
        msg.name = self.mongo_union.name
        msg.bulletin = self.mongo_union.bulletin
        msg.level = self.mongo_union.level
        msg.contribute_points = self.mongo_union.contribute_points
        msg.current_member_amount = self.current_member_amount
        msg.max_member_amount = self.max_member_amount
        msg.rank = UnionBattle(self.char_id).get_order()

        return msg


    def send_notify(self, to_owner=False):
        from core.union.member import Member
        msg = protomsg.UnionNotify()
        msg.in_union = True
        msg.union.MergeFrom(self.make_basic_information())
        msg.leader = self.mongo_union.owner

        for mid in self.member_list:
            msg_member = msg.members.add()
            msg_member.MergeFrom(Member(mid).make_member_message())

        if to_owner:
            char_id = self.mongo_union.owner
        else:
            char_id = self.char_id
        publish_to_char(char_id, pack_msg(msg))


class UnionDummy(object):
    def __init__(self, char_id):
        self.char_id = char_id

    def send_notify(self):
        msg = protomsg.UnionNotify()
        msg.in_union = False
        publish_to_char(self.char_id, pack_msg(msg))


class UnionMember(UnionBase):
    """
    工会成员可以进行的操作
    """
    pass


class UnionOwner(UnionBase):
    """
    工会相关，只有会长才能进行的操作
    """
    def is_member(self, char_id):
        # 角色char_id是否是成员
        return char_id in self.member_list


    def find_next_owner(self):
        # TODO
        members = self.member_list
        if self.char_id in members:
            members.remove(self.char_id)
        if members:
            return members[0]
        return None


    def get_battle_members(self):
        # 获取可参加工会战的会员
        now = arrow.utcnow().timestamp
        hours24 = 24 * 3600
        checkin_limit = now - hours24

        members = []
        for m in MongoUnionMember.objects.filter(joined=self.union_id):
            if m.last_checkin_timestamp >= checkin_limit:
                members.append(m.id)

        if self.char_id in members:
            members.remove(self.char_id)

        members.insert(0, self.char_id)
        return members

    def agree_join(self, char_id):
        # 同意申请
        if not self.is_applied(char_id):
            raise SanguoException(
                    errormsg.UNION_CANNOT_AGREE_NOT_APPLIED,
                    self.char_id,
                    "Union add member",
                    "char {0} not applied".format(char_id)
                    )

        self.add_member(char_id)

    def refuse_join(self, char_id):
        # 拒绝
        from core.union.member import Member
        m = Member(char_id)
        if self.union_id in m.mongo_union_member.applied:
            m.mongo_union_member.applied.remove(self.union_id)
            m.mongo_union_member.save()

        self.send_apply_list_notify()
        UnionList.send_list_notify(char_id)

    def add_member(self, char_id):
        # 添加成员
        from core.union.member import Member
        if self.current_member_amount >= self.max_member_amount:
            raise SanguoException(
                    errormsg.UNION_CANNOT_JOIN_FULL,
                    self.char_id,
                    "Union add member",
                    "full. {0} >= {1}".format(self.current_member_amount, self.max_member_amount)
                    )

        if not isinstance(Union(char_id), UnionDummy):
            raise SanguoException(
                errormsg.UNION_CANNOT_AGREE_JOIN,
                self.char_id,
                "Union Apply Join",
                "char {0} already in union".format(char_id)
            )

        Member(char_id).join_union(self.union_id)
        self.send_notify()
        Union(char_id).send_notify()
        UnionList.send_list_notify(char_id)


    def kick_member(self, member_id):
        # 踢人
        from core.union.member import Member
        if not self.is_member(member_id):
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                self.char_id,
                "Union Kick Member",
                "char {0} is not member of union {1}".format(member_id, self.union_id)
            )

        Member(member_id).quit_union()
        self.send_notify()
        Union(member_id, self.union_id).send_notify()


    def quit(self):
        # 主动退出
        super(UnionOwner, self).quit()
        next_owner = self.find_next_owner()
        if not next_owner:
            self.mongo_union.delete()
        else:
            self.mongo_union.owner = next_owner
            self.mongo_union.save()

        Union(self.char_id).send_notify()


    def transfer(self, member_id):
        # 转让会长
        if not self.is_member(member_id):
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                self.char_id,
                "Union Transfer",
                "{0} is not member of union {1}".format(member_id, self.union_id)
            )

        self.mongo_union.owner = member_id
        self.mongo_union.save()

        Union(self.char_id, self.union_id).send_notify()
        Union(member_id, self.union_id).send_notify()


    def add_contribute_points(self, point):
        self.mongo_union.contribute_points += point

        to_next_level_contributes_needs = UNION_LEVEL[self.mongo_union.level].contributes_needs

        if self.mongo_union.level >= MAX_UNION_LEVEL:
            self.mongo_union.level = MAX_UNION_LEVEL
            if self.mongo_union.contribute_points >= to_next_level_contributes_needs:
                self.mongo_union.contribute_points = to_next_level_contributes_needs
        else:
            if self.mongo_union.contribute_points >= to_next_level_contributes_needs:
                self.mongo_union.contribute_points -= to_next_level_contributes_needs
                self.mongo_union.level += 1

        self.mongo_union.save()
        self.send_notify()


    def modify(self, bulletin):
        self.mongo_union.bulletin = bulletin
        self.mongo_union.save()
        self.send_notify()


    def send_apply_list_notify(self):
        msg = protomsg.UnionApplyListNotify()

        for c in self.applied_list:
            msg_char = msg.chars.add()
            msg_char.MergeFrom(create_character_infomation_message(c))

        publish_to_char(self.char_id, pack_msg(msg))




class UnionList(object):
    @staticmethod
    def send_list_notify(char_id):
        all_unions = MongoUnion.objects.all()
        all_unions = sorted(all_unions, key=lambda item: (-item.level, -item.contribute_points))

        msg = protomsg.UnionListNotify()
        for u in all_unions:
            union = Union(char_id, u.id)
            msg_union = msg.unions.add()
            msg_union.union.MergeFrom(union.make_basic_information())
            msg_union.applied = union.is_applied(char_id)

        publish_to_char(char_id, pack_msg(msg))
