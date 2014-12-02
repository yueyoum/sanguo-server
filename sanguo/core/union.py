# -*- coding: utf-8 -*-
"""
Author:        Wang Chao <yueyoum@gmail.com>
Filename:      union.py
Date created:  2014-12-01 14:20:10
Description:

"""

from mongoengine import DoesNotExist
from core.mongoscheme import MongoUnion, MongoUnionMember
from core.exception import SanguoException
from core.msgfactory import create_character_infomation_message
from core.msgpipe import publish_to_char
from core.resource import Resource

from preset.settings import (
        UNION_NAME_MAX_LENGTH,
        UNION_DES_MAX_LENGTH,
        UNION_DEFAULT_DES,
        UNION_CREATE_NEEDS_SYCEE,
        )

from preset import errormsg


from utils import pack_msg
from utils.functional import id_generator



import protomsg


class UnionMember(object):
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
            self.mongo_union_member.save()

    @property
    def checkin_total_amount(self):
        # FIXME
        return 10

    @property
    def checkin_current_amount(self):
        return self.mongo_union_member.checkin_times

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

    def is_applied(self, union_id):
        # 是否申请过union_id的工会
        return union_id in self.mongo_union_member.applied

    def apply_join(self, union_id):
        # 申请加入
        if union_id not in self.mongo_union_member.applied:
            self.mongo_union_member.applied.append(union_id)
            self.mongo_union_member.save()

        UnionManager(self.char_id).send_list_notify()

    def join_union(self, union_id):
        # 加入工会的后续设置
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
        self.mongo_union_member.save()
        self.send_personal_notify()



class Union(object):
    """
    工会
    玩家自己创建或者加入的工会对象
    工会管理相关操作
    """
    def __init__(self, char_id, union_id):
        self.char_id = char_id
        self.union_id = union_id
        self.mongo_union = MongoUnion.objects.get(id=union_id)

        self.belong_to_self = self.char_id == self.mongo_union.owner

    @property
    def applied_list(self):
        # 申请者ID列表
        mongo_members = MongoUnionMember.objects.filter(applied=self.union_id)
        return [i.id for i in mongo_members]

    @property
    def max_member_amount(self):
        # FIXME
        return 10

    @property
    def current_member_amount(self):
        return MongoUnionMember.objects.filter(joined=self.union_id).count()


    def is_applied(self, char_id):
        # 角色char_id是否申请过
        return UnionMember(char_id).is_applied(self.union_id)


    def add_member(self, char_id):
        # 添加成员
        if not self.is_applied(char_id):
            raise SanguoException(
                    errormsg.UNION_CANNOT_AGREE_NOT_APPLIED,
                    self.char_id,
                    "Union add member",
                    "char {0} not applied".format(char_id)
                    )


        if self.current_member_amount >= self.max_member_amount:
            raise SanguoException(
                    errormsg.UNION_CANNOT_JOIN_FULL,
                    self.char_id,
                    "Union add member",
                    "full. {0} >= {1}".format(self.current_member_amount, self.max_member_amount)
                    )

        UnionMember(self.char_id).join_union(self.union_id)


    def modify(self, bulletin):
        self.mongo_union.bulletin = bulletin
        self.mongo_union.save()
        self.send_notify()


    def make_basic_information(self):
        msg = protomsg.UnionBasicInformation()
        msg.id = self.mongo_union.id
        msg.name = self.mongo_union.name
        msg.bulletin = self.mongo_union.bulletin
        msg.level = self.mongo_union.level
        msg.contribute_points = self.mongo_union.contribute_points
        msg.current_member_amount = self.current_member_amount
        msg.max_member_amount = self.max_member_amount

        return msg


    def send_notify(self):
        msg = protomsg.UnionNotify()
        msg.union.MergeFrom(self.make_basic_information())
        msg.leader = self.mongo_union.owner

        for m in MongoUnionMember.objects.filter(joined=self.union_id):
            msg_member = msg.members.add()
            msg_member.MergeFrom(UnionMember(m.id).make_member_message())

        publish_to_char(self.char_id, pack_msg(msg))

    def send_personal_information_notify(self):
        member = UnionMember(self.char_id)
        member.send_personal_notify()



class UnionManager(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            union_member = MongoUnionMember.objects.get(id=char_id)
            if not union_member.joined:
                self.union = None
            else:
                self.union = Union(char_id, union_member.joined)
        except DoesNotExist:
            self.union = None


    def create(self,name):
        if self.union:
            raise SanguoException(
                    errormsg.UNION_CANNOT_CREATE_ALREADY_IN,
                    self.char_id,
                    "Union Create",
                    "already created"
                    )


        if len(name) > UNION_NAME_MAX_LENGTH:
            raise SanguoException(
                    errormsg.UNION_NAME_TOO_LONG,
                    self.char_id,
                    "Union Create",
                    "name too long: {0}".format(name.encode('utf-8'))
                    )


        if MongoUnion.objects.filter(name=name).count() > 0:
            raise SanguoException(
                    errormsg.UNION_NAME_ALREADY_EXIST,
                    self.char_id,
                    "Union Create",
                    "name already exist: {0}".format(name.encode('utf-8'))
                    )


        resource = Resource(self.char_id, "Union Create")

        with resource.check(sycee=-UNION_CREATE_NEEDS_SYCEE):
            new_id = id_generator('union')[0]
            mu = MongoUnion(id=new_id)
            mu.owner = self.char_id
            mu.name = name
            mu.bulletin = UNION_DEFAULT_DES
            mu.level = 0
            mu.contribute_points = 0
            mu.save()
            UnionMember(self.char_id).join_union(new_id)

        Union(self.char_id, new_id).send_notify()


    def modify(self, union_id, bulletin):
        if not self.union:
            raise SanguoException(
                    errormsg.UNION_NOT_EXIST,
                    self.char_id,
                    "Union Modify",
                    "union not eixst: {0}".format(union_id)
                    )

        if len(bulletin) > UNION_DES_MAX_LENGTH:
            raise SanguoException(
                    errormsg.UNION_DES_TOO_LONG,
                    self.char_id,
                    "Union Modify",
                    "union des too long: {0}, {1}".format(union_id, bulletin.encode('utf-8'))
                    )

        if not self.union.belong_to_self:
            raise SanguoException(
                    errormsg.INVALID_OPERATE,
                    self.char_id,
                    "Union Modify",
                    "union {0} not belong to self".format(union_id)
                    )

        self.union.modify(bulletin)


    def apply_join(self, union_id):
        # 发出加入申请
        if self.union:
            raise SanguoException(
                    errormsg.UNION_CANNOT_JOIN_ALREADY_IN,
                    self.char_id,
                    "Union Join",
                    "already in union: {0}".format(self.union.union_id)
                    )

        UnionMember(self.char_id).apply_join(union_id)


    def agree_join(self, char_id):
        # 接受加入申请
        if not self.union or not self.union.belong_to_self:
            raise SanguoException(
                    errormsg.INVALID_OPERATE,
                    self.char_id,
                    "Union Apply Join",
                    "char {0} has no union or not the owner".format(self.char_id)
                    )

        um = UnionManager(char_id)
        if um.union:
            raise SanguoException(
                    errormsg.UNION_CANNOT_AGREE_JOIN,
                    self.char_id,
                    "Union Apply Join",
                    "char {0} already in union {1}".format(char_id, um.union.union_id)
                    )

        self.union.add_member(char_id)
        self.send_apply_list_notify()

    def refuse_join(self, char_id):
        # 拒绝
        if not self.union or not self.union.belong_to_self:
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                self.char_id,
                "Union Refuse Join",
                "char {0} has no union or not the owner".format(self.char_id)
            )

        m = UnionMember(char_id)
        if self.union.union_id in m.mongo_union_member.applied:
            m.mongo_union_member.applied.remove(self.union.union_id)
            m.mongo_union_member.save()

        self.send_apply_list_notify()


    def send_apply_list_notify(self):
        if not self.union or not self.union.belong_to_self:
            return

        msg = protomsg.UnionApplyListNotify()
        for c in self.union.applied_list:
            msg_char = msg.chars.add()
            msg_char.MergeFrom(create_character_infomation_message(c))

        publish_to_char(self.char_id, pack_msg(msg))


    def send_list_notify(self):
        all_unions = MongoUnion.objects.all()
        all_unions = sorted(all_unions, key=lambda item: (-item.level, -item.contribute_points))

        msg = protomsg.UnionListNotify()
        for u in all_unions:
            union = Union(self.char_id, u.id)
            msg_union = msg.unions.add()
            msg_union.union.MergeFrom(union.make_basic_information())
            msg_union.applied = union.is_applied(self.char_id)

        publish_to_char(self.char_id, pack_msg(msg))


    def send_notify(self):
        self.send_list_notify()
        self.send_apply_list_notify()

        if not self.union:
            return

        self.union.send_notify()
        self.union.send_personal_information_notify()


