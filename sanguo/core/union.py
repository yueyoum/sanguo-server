# -*- coding: utf-8 -*-
"""
Author:        Wang Chao <yueyoum@gmail.com>
Filename:      union.py
Date created:  2014-12-01 14:20:10
Description:

"""

import random
import arrow

from mongoengine import DoesNotExist, Q
from core.mongoscheme import MongoUnion, MongoUnionMember, MongoUnionBoss, MongoEmbeddedUnionBoss, MongoEmbeddedUnionBossLog
from core.exception import SanguoException
from core.msgfactory import create_character_infomation_message
from core.msgpipe import publish_to_char
from core.resource import Resource
from core.signals import global_buff_changed_signal
from core.resource import Resource
from core.character import Char
from core.battle import PVE
from core.battle.hero import InBattleHero
from core.battle.battle import Ground

from utils import pack_msg
from utils.functional import id_generator

from preset.settings import (
        UNION_NAME_MAX_LENGTH,
        UNION_DES_MAX_LENGTH,
        UNION_DEFAULT_DES,
        UNION_CREATE_NEEDS_SYCEE,
        )

from preset import errormsg

from preset.data import UNION_STORE, UNION_CHECKIN, UNION_BOSS, HORSE, STUFFS


import protomsg


BUFFS = [11,12,13]
BUFF_NAME_TABLE = {
    11: 'attack',
    12: 'defense',
    13: 'hp',
}
UNION_STORE_BUFF_STORE_ID_DICT = {}
for _k, _v in UNION_STORE.items():
    if _v.tp in BUFFS:
        UNION_STORE_BUFF_STORE_ID_DICT[_v.tp] = _k


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
            self.mongo_union_member.buy_buff_times = {}
            self.mongo_union_member.save()

    @property
    def checkin_total_amount(self):
        # FIXME
        return 10

    @property
    def checkin_current_amount(self):
        return self.mongo_union_member.checkin_times

    def checkin(self):
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

            self.mongo_union_member.coin += c.got_coin
            self.mongo_union_member.contribute_points += c.got_contributes
            self.mongo_union_member.save()
        self.send_personal_notify()


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

    def add_coin(self, coin):
        self.mongo_union_member.coin += coin
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
    # union_need_exist: True | False
    # err_msg: None | Msg. 如果是None表示检测失败后就返回None，否则raise异常
    def deco(func):
        def wrap(self, *args, **kwargs):
            res = self.union is not None
            error = False
            if union_need_exist and not res:
                error = True
            if not union_need_exist and res:
                error = True

            if error:
                if err_msg is None:
                    return None

                raise SanguoException(
                    err_msg,
                    self.char_id,
                    func_name,
                    des
                )

            return func(self, *args, **kwargs)
        return wrap
    return deco


class UnionLoadBase(object):
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


class UnionManager(UnionLoadBase):
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
        UnionBattle(self.char_id).send_notify()


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


class UnionStore(UnionLoadBase):
    def __init__(self, char_id):
        super(UnionStore, self).__init__(char_id)
        self.union_member = UnionMember(char_id)

    def get_add_buffs_with_resource_id(self):
        cur_buy_times = self.buff_cur_buy_times

        def _get_value(buff_id):
            store_id = UNION_STORE_BUFF_STORE_ID_DICT[buff_id]
            value = UNION_STORE[store_id].value * cur_buy_times[buff_id]
            return value

        return {k: _get_value(k) for k in BUFFS}

    def get_add_buffs_with_string_name(self):
        buffs = self.get_add_buffs_with_resource_id()
        return {BUFF_NAME_TABLE[k]: v for k, v in buffs.items()}


    @property
    def buff_max_buy_times(self):
        # TODO
        return 10

    @property
    def buff_cur_buy_times(self):
        cur_times = {}
        for i in BUFFS:
            cur_times[i] = self.union_member.mongo_union_member.buy_buff_times.get(str(i), 0)

        return cur_times

    @_union_manager_check(True, errormsg.INVALID_OPERATE, "UnionStore Buy", "has no union")
    def buy(self, _id, amount):
        try:
            item = UNION_STORE[_id]
        except KeyError:
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                "UnionStore Buy",
                "item {0} not exist".format(_id)
            )

        self.union_member.check_coin(item.union_coin, raise_exception=True, func_name="UnionStore Buy")

        if item.tp in BUFFS:
            self._buy_buff(_id, item.tp, amount)
        elif item.tp == 10:
            self._buy_horse(_id, item.value, amount)
        else:
            self._buy_items(_id, item.value, amount)

        self.union_member.cost_coin(item.union_coin)


    def _buy_buff(self, _id, item_id, amount):
        cur_buy_times = self.buff_cur_buy_times
        if cur_buy_times[item_id] + amount > self.buff_max_buy_times:
            raise SanguoException(
                errormsg.UNION_STORE_BUY_REACH_MAX_TIMES,
                self.char_id,
                "UnionStore Buy",
                "buff {0} has reached the max buy times {1}".format(item_id, self.buff_max_buy_times)
            )

        self.union_member.mongo_union_member.buy_buff_times[str(item_id)] = cur_buy_times[item_id] + amount
        self.union_member.mongo_union_member.save()

        self.send_notify()

        global_buff_changed_signal.send(
            sender=None,
            char_id=self.char_id
        )



    def _buy_horse(self, _id, item_id, amount):
        if item_id not in HORSE:
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                self.char_id,
                "UnionStore Buy",
                "horse {0} not exist".format(item_id)
            )

        resources = Resource(self.char_id, "UnionStore Buy")
        resources.add(horses=[(item_id, amount)])

    def _buy_items(self, _id, item_id, amount):
        if item_id not in STUFFS:
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                self.char_id,
                "UnionStore Buy",
                "stuff {0} not exist".format(item_id)
            )

        resources = Resource(self.char_id, "UnionStore Buy")
        resources.add(stuffs=[(item_id, amount)])

    def send_notify(self):
        msg = protomsg.UnionStoreNotify()
        max_times = self.buff_max_buy_times
        cur_times = self.buff_cur_buy_times

        add_buffs = self.get_add_buffs_with_resource_id()

        for i in BUFFS:
            msg_buff = msg.buffs.add()
            msg_buff.id = i
            msg_buff.max_times = max_times
            msg_buff.cur_times = cur_times[i]
            msg_buff.add_value = add_buffs[i]

        publish_to_char(self.char_id, pack_msg(msg))


class UnionBattleRecord(object):
    # 战斗记录
    class TeamEnd(Exception):
        pass


    class Team(object):
        def __init__(self, team):
            self.team = team
            self.members = team[:]

        def get(self):
            try:
                cid = self.team.pop(0)
                c = Char(cid)
                c.union_battle_power = c.power
                return c
            except IndexError:
                raise UnionBattleRecord.TeamEnd()

    def __init__(self, my_char_id, my_union_id, rival_char_id, rival_union_id):
        self.my_char_id = my_char_id
        self.rival_char_id = rival_char_id

        self.my_union = Union(my_char_id, my_union_id)
        self.rival_union = Union(rival_char_id, rival_union_id)


        self.my_union_name = self.my_union.mongo_union.name
        self.rival_union_name = self.rival_union.mongo_union.name

        self.my_team = self.Team(self.my_union.get_battle_members())
        self.rival_team = self.Team(self.rival_union.get_battle_members())

        self.start_at = arrow.utcnow().timestamp
        self.initiative = True

        self.logs = []

    def start(self):
        my_char = self.my_team.get()
        rival_char = self.rival_team.get()

        while True:
            if my_char.union_battle_power >= rival_char.union_battle_power:
                new_union_battle_power = pow(
                    pow(my_char.union_battle_power, 2) - pow(rival_char.union_battle_power, 2),
                    0.5
                ) + 1

                percent = int( float(new_union_battle_power) / my_char.union_battle_power * 100 )

                my_char.union_battle_power = new_union_battle_power

                self.logs.append((
                    my_char.mc.name, rival_char.mc.name, True, percent
                ))


                try:
                    rival_char = self.rival_team.get()
                except self.TeamEnd:
                    self.win = True
                    break

            else:
                new_union_battle_power = pow(
                    pow(rival_char.union_battle_power, 2) - pow(my_char.union_battle_power, 2),
                    0.5
                ) + 1

                percent = int( float(new_union_battle_power) / rival_char.union_battle_power * 100 )

                rival_char.union_battle_power = new_union_battle_power

                self.logs.append((
                    my_char.mc.name, rival_char.mc.name, False, percent
                ))

                try:
                    my_char = self.my_team.get()
                except self.TeamEnd:
                    self.win = False
                    break


    def make_record_msg(self):
        msg = protomsg.UnionBattleRecord()
        msg.rival_name = self.rival_union_name
        msg.initiative = self.initiative
        msg.win = self.win
        msg.timestamp = self.start_at
        # FIXME
        msg.score = 10

        for name_1, name_2, win, hp in self.logs:
            msg_log = msg.logs.add()
            msg_log.my_name = name_1
            msg_log.rival_name = name_2
            msg_log.win = win
            msg_log.hp = hp

        return msg

    def make_other_side_record_msg(self):
        msg = protomsg.UnionBattleRecord()
        msg.rival_name = self.my_union_name
        msg.initiative = not self.initiative
        msg.win = not self.win
        msg.timestamp = self.start_at
        # FIXME
        msg.score = -10

        for name_1, name_2, win, hp in self.logs:
            msg_log = msg.logs.add()
            msg_log.my_name = name_2
            msg_log.rival_name = name_1
            msg_log.win = not win
            msg_log.hp = hp

        return msg


    def save(self):
        my_msg = self.make_record_msg()
        rival_msg = self.make_other_side_record_msg()

        if len(self.my_union.mongo_union.battle_records) >= 10:
            self.my_union.mongo_union.battle_records.pop(0)
        self.my_union.mongo_union.battle_records.append(my_msg.SerializeToString())
        self.my_union.mongo_union.save()

        if len(self.rival_union.mongo_union.battle_records) >= 10:
            self.rival_union.mongo_union.battle_records.pop(0)
        self.rival_union.mongo_union.battle_records.append(rival_msg.SerializeToString())
        self.rival_union.mongo_union.save()

        return my_msg





class UnionBattle(UnionLoadBase):
    # def __init__(self, char_id):
    #     super(UnionBattle, self).__init__(char_id)
    #     # if not self.union.belong_to_self:
    #     #     self.union = None

    @staticmethod
    def get_board():
        unions = MongoUnion.objects.all().order_by('-score')

        board = []
        order = 1

        for u in unions:
            c = Char(u.owner)
            data = {
                'order': order,
                'score': u.score,
                'name': u.name,
                'level': u.level,
                'leader_name': c.mc.name,
                'leader_avatar': c.leader_oid
            }

            board.append(data)
            order += 1

        return board

    @property
    def max_battle_times(self):
        # TODO
        return 10

    @property
    def cur_battle_times(self):
        return self.union.mongo_union.battle_times

    def find_rival(self):
        score = self.union.mongo_union.score

        def _find_rival(score_diff):
            condition = Q(id__ne=self.union.union_id)
            if score_diff is not None:
                condition = condition & Q(score__gte=score-score_diff) & Q(score__lte=score+score_diff)

            unions = MongoUnion.objects.filter(condition)
            if unions:
                return random.choice(unions)
            return None

        rival_union = _find_rival(30)
        if not rival_union:
            rival_union = _find_rival(100)
            if not rival_union:
                rival_union = _find_rival(None)

        return rival_union


    @_union_manager_check(True, errormsg.UNION_NOT_EXIST, "UnionBattle Start", "has no union")
    def start_battle(self):
        if not self.union.belong_to_self:
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                self.char_id,
                "UnionBattle Start",
                "no permission"
            )


        rival_union = self.find_rival()
        if not rival_union:
            raise SanguoException(
                errormsg.UNION_BATTLE_NO_RIVAL,
                self.char_id,
                "UnionBattle Start",
                "no rival"
            )

        record = UnionBattleRecord(self.union.char_id, self.union.union_id, rival_union.owner, rival_union.id)
        record.start()
        msg = record.save()

        self.send_notify()
        return msg

    @_union_manager_check(True, errormsg.UNION_NOT_EXIST, "UnionBattle Start", "has no union")
    def get_records(self):
        return self.union.mongo_union.battle_records


    @_union_manager_check(True, None, "UnionBattle")
    def send_notify(self):
        msg = protomsg.UnionBattleNotify()
        msg.score = self.union.mongo_union.score

        order = MongoUnion.objects.filter(score__gt=msg.score).count()

        msg.order = order + 1
        msg.in_battle_members = len(self.union.get_battle_members())
        msg.remained_battle_times = self.max_battle_times - self.cur_battle_times

        publish_to_char(self.char_id, pack_msg(msg))


    @_union_manager_check(True, errormsg.UNION_NOT_EXIST, "UnionBattle Board")
    def make_board_msg(self):
        msg = protomsg.UnionBattleBoardResponse()
        msg.ret = 0
        for data in UnionBattle.get_board():
            msg_union = msg.union.add()
            msg_union.order = data['order']
            msg_union.score = data['score']
            msg_union.name = data['name']
            msg_union.level = data['level']
            msg_union.leader_name = data['leader_name']
            msg_union.leader_avatar = data['leader_avatar']

        return msg




class UnionBoss(UnionLoadBase):
    def __init__(self, char_id):
        super(UnionBoss, self).__init__(char_id)
        if self.valid:
            self.load_data()

    def load_data(self):
        try:
            self.mongo_boss = MongoUnionBoss.objects.get(id=self.union.union_id)
        except DoesNotExist:
            self.mongo_boss = MongoUnionBoss(id=self.union.union_id)
            self.mongo_boss.save()

        self.union_member = UnionMember(self.char_id)


    @property
    def valid(self):
        return self.union is not None

    @property
    def max_times(self):
        # FIXME
        return 10

    @property
    def cur_times(self):
        return self.union_member.mongo_union_member.boss_times

    def incr_battle_times(self):
        self.union_member.mongo_union_member.boss_times += 1
        self.union_member.mongo_union_member.save()

    @_union_manager_check(True, errormsg.UNION_NOT_EXIST, "UnionBoss Start", "has no union")
    def start(self, boss_id):
        try:
            boss = UNION_BOSS[boss_id]
        except KeyError:
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                self.char_id,
                "UnionBoss Start",
                "boss {0} not exist".format(boss_id)
            )

        # TODO union level check
        meb = MongoEmbeddedUnionBoss()
        meb.start_at = arrow.utcnow().timestamp
        meb.hp = boss.hp
        meb.killer = 0
        meb.logs = []

        self.mongo_boss.opened[str(boss_id)] = meb
        self.mongo_boss.save()


    @_union_manager_check(True, errormsg.UNION_NOT_EXIST, "UnionBoss Battle", "ha no union")
    def battle(self, boss_id):
        try:
            this_boss = self.mongo_boss.opened[str(boss_id)]
        except KeyError:
            raise SanguoException(
                errormsg.UNION_BOSS_NOT_STARTED,
                self.char_id,
                "UnionBoss Battle",
                "boss not started {0}".format(boss_id)
            )

        if this_boss.hp <= 0:
            raise SanguoException(
                errormsg.UNION_BOSS_DEAD,
                self.char_id,
                "UnionBoss Battle",
                "boss dead {0}".format(boss_id)
            )

        msg = protomsg.Battle()
        battle = UnionBossBattle(self.char_id, boss_id, msg, this_boss.hp)
        remained_hp = battle.start()

        if remained_hp == 0:
            killer = self.char_id
        else:
            killer = 0

        this_boss.hp = remained_hp
        this_boss.killer = killer

        eubl = MongoEmbeddedUnionBossLog()
        eubl.char_id = self.char_id
        eubl.damage = battle.get_total_damage()

        this_boss.logs.append(eubl)
        self.mongo_boss.save()

        self.incr_battle_times()

        return msg


    @_union_manager_check(True, errormsg.UNION_NOT_EXIST, "UnionBoss Get Log", "has no union")
    def make_log_message(self, boss_id):
        try:
            this_boss = self.mongo_boss.opened[str(boss_id)]
        except KeyError:
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                self.char_id,
                "UnionBoss Get Log",
                "no log for boss {0}".format(boss_id)
            )

        hp = float(UNION_BOSS[boss_id].hp)

        msg = protomsg.UnionBossGetLogResponse()
        msg.ret = 0
        msg.boss_id = boss_id
        msg.killer = this_boss.killer or 0
        for log in msg.logs:
            msg_log = msg.logs.add()
            msg_log.char_id = log.char_id
            msg_log.char_name = Char(log.char_id).mc.name
            msg_log.damage = log.damage
            msg_log.precent = int(log.damage/hp * 100)

        return msg



    @_union_manager_check(True, errormsg.UNION_NOT_EXIST, "UnionBoss Response", "has no union")
    def make_boss_response(self):
        msg = protomsg.UnionBossResponse()
        msg.ret = 0
        msg.remained_times = self.max_times - self.cur_times

        # FIXME filter by union level
        for b in UNION_BOSS.keys():
            msg_boss = msg.bosses.add()
            msg_boss.id = b

            if str(b) not in self.mongo_boss.opened:
                msg_boss.hp = UNION_BOSS[b].hp
                msg_boss.status = protomsg.UnionBossResponse.Boss.INACTIVE
            else:
                this_boss = self.mongo_boss.opened[str(b)]
                msg_boss.hp = this_boss.hp

                if this_boss.hp <= 0:
                    msg_boss.status = protomsg.UnionBossResponse.Boss.DEAD
                else:
                    msg_boss.status = protomsg.UnionBossResponse.Boss.ACTIVE

        return msg



class BattleBoss(InBattleHero):
    HERO_TYPE = 3
    def __init__(self, boss_id):
        info = UNION_BOSS[boss_id]
        self.id = boss_id
        self.real_id = boss_id
        self.original_id = boss_id

        self.attack = info.attack
        self.defense = info.defense
        self.hp = info.hp
        self.crit = info.crit
        self.dodge = 0

        self.anger = 0
        self.default_skill = info.default_skill
        self.skills = [info.skill]
        self.skill_release_rounds = info.skill_rounds
        self.level = 0

        super(BattleBoss, self).__init__()

    def find_skill(self, skills):
        if self._round / self.skill_release_rounds == 0:
            return skills
        return [self.default_skill]

    def real_damage_value(self, damage, target):
        return damage


class UnionBossBattle(PVE):
    BATTLE_TYPE = 'UNION_BOSS'
    def __init__(self, my_id, rival_id, msg, boss_init_hp):
        super(UnionBossBattle, self).__init__(my_id, rival_id, msg)
        self.msg.rival_power /= 3
        self.boss_init_hp = boss_init_hp

    def load_rival_heros(self):
        bosses = [
            0, BattleBoss(self.rival_id), 0,
            0, BattleBoss(self.rival_id), 0,
            0, BattleBoss(self.rival_id), 0,
        ]

        rival_heros = []
        for b in bosses:
            if b == 0:
                rival_heros.append(None)
            else:
                rival_heros.append(b)

        return rival_heros

    def get_rival_name(self):
        return UNION_BOSS[self.rival_id].name

    def start(self):
        msgs = [self.msg.first_ground, self.msg.second_ground, self.msg.third_ground]
        win_count = 0

        def _recover_hp(i):
            boss = self.rival_heros[i]
            _hp = int( boss.total_damage_value * 0.05 )
            boss.hp += _hp
            return boss.hp

        for index in range(3):
            # index = 0, 1 ,2
            # boss = self.rival_heros [1, 4, 7]
            # old_boss = self.rival_heros [ (index-1)*3 + 1 ]
            # cur_boss = self.rival_heros [ index*3 + 1 ]
            my_heros = self.my_heros[index*3:index*3+3]
            rival_heros = self.rival_heros[index*3:index*3+3]
            if index == 0:
                rival_heros[1].hp = self.boss_init_hp
            else:
                # 生命值继承自上一场战斗
                rival_heros[1].hp = _recover_hp((index-1)*3+1)

            g = Ground(my_heros, rival_heros, msgs[index])
            g.index = index + 1
            win = g.start()
            if win:
                win_count += 1

        if win_count > 2:
            self.msg.self_win = True
        else:
            self.msg.self_win = False

        if self.msg.self_win:
            return 0
        return _recover_hp(7)

    def get_total_damage(self):
        return self.rival_heros[1].total_damage_value + \
            self.rival_heros[4].total_damage_value + \
            self.rival_heros[7].total_damage_value

