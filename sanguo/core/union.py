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

    def quit_union(self):
        # 退出工会
        self.mongo_union_member.joined = 0
        self.mongo_union_member.contribute_points = 0
        self.mongo_union_member.position = 1
        self.mongo_union_member.save()
        self.send_personal_notify()



def _union_permission(func_name):
    def deco(func):
        def wrap(self, *args, **kwargs):
            if not self.belong_to_self:
                raise SanguoException(
                    errormsg.INVALID_OPERATE,
                    self.char_id,
                    func_name,
                    "no permission"
                )

            return func(self, *args, **kwargs)
        return wrap
    return deco


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
    def member_list(self):
        # 成员ID列表
        members = MongoUnionMember.objects.filter(joined=self.union_id)
        return [i.id for i in members]

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


    @_union_permission("Union Add Member")
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

        UnionMember(char_id).join_union(self.union_id)
        self.send_notify()


    @_union_permission("Union Kickout")
    def kick_member(self, member_id):
        # 踢人
        if not self.is_member(member_id):
            return

        UnionMember(member_id).quit_union()
        self.send_notify()

    @_union_permission("Union Quit")
    def quit(self):
        # 自己主动退出
        if self.belong_to_self:
            self._quit_owner()
        else:
            self._quit_member()

        self.mongo_union = None

    def _quit_owner(self):
        # 会长退出
        UnionMember(self.char_id).quit_union()
        next_owner = self.find_next_owner()
        if not next_owner:
            self.mongo_union.delete()
        else:
            self.mongo_union.owner = next_owner
            self.mongo_union.save()

    def _quit_member(self):
        # 成员退出
        UnionMember(self.char_id).quit_union()


    @_union_permission("Union Transfer")
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
        self.belong_to_self = False

        self.send_notify()
        Union(member_id, self.union_id).send_notify()


    @_union_permission("Union Modify")
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

        for mid in self.member_list:
            msg_member = msg.members.add()
            msg_member.MergeFrom(UnionMember(mid).make_member_message())

        publish_to_char(self.char_id, pack_msg(msg))

    def send_personal_information_notify(self):
        member = UnionMember(self.char_id)
        member.send_personal_notify()


def _union_manager_check(union_need_exist, err_msg, func_name, des=""):
    def deco(func):
        def wrap(self, *args, **kwargs):
            res = self.union is not None
            error = False
            if union_need_exist and not res:
                error = True
            if not union_need_exist and res:
                error = True

            if error:
                raise SanguoException(
                    err_msg,
                    self.char_id,
                    func_name,
                    des
                )

            return func(self, *args, **kwargs)
        return wrap
    return deco

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


    @_union_manager_check(False, errormsg.UNION_CANNOT_CREATE_ALREADY_IN, "Union Create", "already in")
    def create(self,name):
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


    @_union_manager_check(True, errormsg.UNION_NOT_EXIST, "Union Modify", "has no union")
    def modify(self, union_id, bulletin):
        if len(bulletin) > UNION_DES_MAX_LENGTH:
            raise SanguoException(
                    errormsg.UNION_DES_TOO_LONG,
                    self.char_id,
                    "Union Modify",
                    "union des too long: {0}, {1}".format(union_id, bulletin.encode('utf-8'))
                    )

        self.union.modify(bulletin)


    @_union_manager_check(False, errormsg.UNION_CANNOT_JOIN_ALREADY_IN, "Union Join", "already in")
    def apply_join(self, union_id):
        # 发出加入申请
        UnionMember(self.char_id).apply_join(union_id)


    @_union_manager_check(True, errormsg.INVALID_OPERATE, "Union Agree Join", "has no union")
    def agree_join(self, char_id):
        # 接受加入申请
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

        UnionManager(char_id).send_notify()

    @_union_manager_check(True, errormsg.INVALID_OPERATE, "Union Refuse Join", "has no union")
    def refuse_join(self, char_id):
        # 拒绝
        m = UnionMember(char_id)
        if self.union.union_id in m.mongo_union_member.applied:
            m.mongo_union_member.applied.remove(self.union.union_id)
            m.mongo_union_member.save()

        self.send_apply_list_notify()
        UnionManager(char_id).send_list_notify()

    @_union_manager_check(True, errormsg.INVALID_OPERATE, "Union Quit", "has no union")
    def quit(self):
        # 主动退出
        self.union.quit()

    @_union_manager_check(True, errormsg.INVALID_OPERATE, "Union Kickout", "has no union")
    def kickout(self, member_id):
        # 踢人
        self.union.kick_member(member_id)


    @_union_manager_check(True, errormsg.INVALID_OPERATE, "Union Transfer", "has no union")
    def transfer(self, member_id):
        # 转让会长
        self.union.transfer(member_id)
        self.send_apply_list_notify(lists=[])


    def send_apply_list_notify(self, lists=None):
        if not self.union or not self.union.belong_to_self:
            return

        msg = protomsg.UnionApplyListNotify()
        if lists is None:
            lists = self.union.applied_list

        for c in lists:
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


