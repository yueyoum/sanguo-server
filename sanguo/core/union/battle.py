# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-12-10'

import arrow
import random

from mongoengine import Q
from core.mongoscheme import MongoUnion

from core.character import Char
from core.exception import SanguoException
from core.msgpipe import publish_to_char
from core.arena import calculate_score

from core.union.union import UnionBase, UnionOwner, Union
from core.union.base import UnionLoadBase, union_instance_check

from utils import pack_msg
from preset import errormsg
from preset.settings import UNION_BATTLE_INITIAL_SCORE, UNION_BATTLE_LOWEST_SCORE

import protomsg



def get_battle_init_score():
    # 竞技场初始化积分
    if MongoUnion.objects.count() == 0:
        return UNION_BATTLE_INITIAL_SCORE
    else:
        score = MongoUnion.objects.all().order_by('score')[0].score
        if score < UNION_BATTLE_LOWEST_SCORE:
            score = UNION_BATTLE_LOWEST_SCORE
        return score



class UnionBattle(UnionLoadBase):
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
        return 1

    @property
    def cur_battle_times(self):
        return self.union.mongo_union.battle_times

    def find_rival_char_id(self):
        score = self.union.mongo_union.score

        def _find_rival(score_diff):
            condition = Q(id__ne=self.union.union_id)
            if score_diff is not None:
                condition = condition & Q(score__gte=score-score_diff) & Q(score__lte=score+score_diff)

            unions = MongoUnion.objects.filter(condition)
            if unions:
                return random.choice(unions).owner
            return None

        rival_char_id = _find_rival(20)
        if not rival_char_id:
            rival_char_id = _find_rival(60)
            if not rival_char_id:
                rival_char_id = _find_rival(None)

        return rival_char_id


    @union_instance_check(UnionOwner, errormsg.UNION_BATTLE_ONLY_STARTED_BY_OWNER, "UnionBattle Start", "not owner")
    def start_battle(self):
        rival_char_id = self.find_rival_char_id()
        if not rival_char_id:
            raise SanguoException(
                errormsg.UNION_BATTLE_NO_RIVAL,
                self.char_id,
                "UnionBattle Start",
                "no rival"
            )

        record = UnionBattleRecord(self.char_id, rival_char_id)
        record.start()
        msg = record.save()

        self.send_notify()

        if msg.win:
            self.after_battle_win()
        else:
            self.after_battle_lose()

        return msg


    def after_battle_win(self):
        # 打赢设置
        pass

    def after_battle_lose(self):
        # 打输设置
        pass


    @union_instance_check(UnionBase, errormsg.UNION_NOT_EXIST, "UnionBattle Get Records", "has no union")
    def get_records(self):
        return self.union.mongo_union.battle_records


    def cron_job(self):
        self.union.mongo_union.battle_times = 0
        self.union.mongo_union.save()
        self.send_notify()


    @union_instance_check(UnionBase, None, "UnionBattle Get Order", "has no union")
    def get_order(self):
        score = self.union.mongo_union.score
        order = MongoUnion.objects.filter(score__gt=score).count()
        return order+1


    @union_instance_check(UnionBase, None, "UnionBattle Send Notify")
    def send_notify(self):
        msg = protomsg.UnionBattleNotify()
        msg.score = self.union.mongo_union.score

        msg.order = self.get_order()
        msg.in_battle_members = len(self.union.get_battle_members())
        msg.remained_battle_times = self.max_battle_times - self.cur_battle_times

        publish_to_char(self.char_id, pack_msg(msg))


    @union_instance_check(UnionBase, errormsg.UNION_NOT_EXIST, "UnionBattle Board", "has no union")
    def make_board_msg(self):
        msg = protomsg.UnionBattleBoardResponse()
        msg.ret = 0
        for data in self.get_board():
            msg_union = msg.union.add()
            msg_union.order = data['order']
            msg_union.score = data['score']
            msg_union.name = data['name']
            msg_union.level = data['level']
            msg_union.leader_name = data['leader_name']
            msg_union.leader_avatar = data['leader_avatar']

        return msg




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
                c.union_battle_power_original = c.power
                return c
            except IndexError:
                raise UnionBattleRecord.TeamEnd()

    def __init__(self, my_char_id, rival_char_id):
        self.my_char_id = my_char_id
        self.rival_char_id = rival_char_id

        self.my_union = Union(my_char_id)
        self.rival_union = Union(rival_char_id)


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

                percent = int( float(new_union_battle_power) / my_char.union_battle_power_original * 100 )

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

                percent = int( float(new_union_battle_power) / rival_char.union_battle_power_original * 100 )

                rival_char.union_battle_power = new_union_battle_power

                self.logs.append((
                    my_char.mc.name, rival_char.mc.name, False, percent
                ))

                try:
                    my_char = self.my_team.get()
                except self.TeamEnd:
                    self.win = False
                    break

        # battle finish
        self.my_new_score = self.my_union.mongo_union.score
        self.rival_new_score = self.rival_union.mongo_union.score

        if self.win:
            self.my_new_score = calculate_score(
                self.my_union.mongo_union.score,
                self.rival_union.mongo_union.score,
                self.win
            )

            self.rival_new_score = calculate_score(
                self.rival_union.mongo_union.score,
                self.my_union.mongo_union.score,
                not self.win
            )


    def make_record_msg(self):
        msg = protomsg.UnionBattleRecord()
        msg.rival_name = self.rival_union_name
        msg.initiative = self.initiative
        msg.win = self.win
        msg.timestamp = self.start_at
        msg.score = self.my_new_score - self.my_union.mongo_union.score

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
        msg.score = self.rival_new_score - self.rival_union.mongo_union.score

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

        self.my_union.mongo_union.score = self.my_new_score
        self.my_union.mongo_union.save()

        if len(self.rival_union.mongo_union.battle_records) >= 10:
            self.rival_union.mongo_union.battle_records.pop(0)
        self.rival_union.mongo_union.battle_records.append(rival_msg.SerializeToString())

        self.rival_union.mongo_union.score = self.rival_new_score
        self.rival_union.mongo_union.save()

        return my_msg







