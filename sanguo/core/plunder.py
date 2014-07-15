# -*- coding: utf-8 -*-


__author__ = 'Wang Chao'
__date__ = '1/22/14'

import random

from mongoscheme import Q, DoesNotExist
from core.character import Char, get_char_ids_by_level_range
from core.battle import PVP
from core.stage import Hang, max_star_stage_id
from core.mongoscheme import MongoHangDoing, MongoPlunder, MongoStage, MongoPlunderChar
from core.exception import SanguoException
from core.counter import Counter
from core.task import Task
from core.formation import Formation
from core.prison import Prison
from core.stage import Stage
from core.resource import Resource
from core.attachment import make_standard_drop_from_template, get_drop, standard_drop_to_attachment_protomsg
from protomsg import Battle as MsgBattle
from protomsg import PlunderNotify
from core.msgpipe import publish_to_char
from utils import pack_msg
from utils.checkers import not_hang_going
from preset.settings import (
    PLUNDER_GET_OFFICIAL_EXP_WHEN_WIN,
    PLUNDER_GOT_POINT,
    PLUNDER_DEFENSE_FAILURE_GOLD,
    PLUNDER_REWARD_NEEDS_POINT,
    PLUNDER_GOT_ITEMS_HOUR,
)
from protomsg import PLUNDER_HERO, PLUNDER_STUFF, PLUNDER_GOLD
from preset import errormsg
from preset.data import STAGES, VIP_MAX_LEVEL, VIP_FUNCTION


class Plunder(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.mongo_plunder = MongoPlunder.objects.get(id=self.char_id)
        except DoesNotExist:
            self.mongo_plunder = MongoPlunder(id=self.char_id)
            self.mongo_plunder.points = 0
            self.mongo_plunder.chars = {}
            self.mongo_plunder.target_char = 0
            self.mongo_plunder.got_reward = []
            self.mongo_plunder.save()


    def get_plunder_list(self):
        """
        @return: [[id, name, power, leader, formation, is_hang], ...]
        @rtype: list
        """
        char = Char(self.char_id)
        cache_char = char.mc
        char_level = cache_char.level

        min_level = max(5, char_level-5)
        max_level = char_level + 5

        choosing_list = get_char_ids_by_level_range(min_level, max_level, exclude_char_ids=[self.char_id])
        if len(choosing_list) < 10:
            min_level = 5
            max_level = char_level + 10
            choosing_list = get_char_ids_by_level_range(min_level, max_level, exclude_char_ids=[self.char_id])

        random.shuffle(choosing_list)
        ids = choosing_list[:10]

        res = []
        for i in ids:
            char = Char(i)
            f = Formation(i)
            res.append([i, char.mc.name, char.power, f.get_leader_oid(), f.in_formation_hero_original_ids(), not not_hang_going(i)])

        self_power = float(Char(self.char_id).power)

        def _get_color(p):
            percent = p / self_power
            if percent <= 0.9:
                return 1
            if percent <= 1.1:
                return 2
            return 3

        self.mongo_plunder.chars = {}
        for _id, _, power, _, _, is_hang in res:
            mpc = MongoPlunderChar()
            mpc.is_hang = is_hang
            mpc.color = _get_color(power)
            self.mongo_plunder.chars[str(_id)] = mpc
        self.mongo_plunder.save()
        return res


    def plunder(self, _id):
        if str(_id) not in self.mongo_plunder.chars:
            raise SanguoException(
                errormsg.PLUNDER_NOT_IN_LIST,
                self.char_id,
                "Plunder Plunder",
                "Plunder, {0} not in plunder list".format(_id)
            )

        counter = Counter(self.char_id, 'plunder')
        if counter.remained_value <= 0:
            char = Char(self.char_id).mc
            if char.vip < VIP_MAX_LEVEL:
                raise SanguoException(
                    errormsg.PLUNDER_NO_TIMES,
                    self.char_id,
                    "Plunder Battle",
                    "Plunder no times. vip current: {0}, max: {1}".format(char.vip, VIP_MAX_LEVEL)
                )
            raise SanguoException(
                errormsg.PLUNDER_NO_TIMES_FINAL,
                self.char_id,
                "Plunder Battle",
                "Plunder no times. vip reach max level {0}".format(VIP_MAX_LEVEL)
            )

        msg = MsgBattle()
        pvp = PVP(self.char_id, _id, msg)
        pvp.start()

        if self.mongo_plunder.chars[str(_id)].is_hang:
            char = Char(self.char_id)
            h = Hang(_id)
            h.plundered(char.cacheobj.name, not msg.self_win)

        t = Task(self.char_id)
        t.trig(3)

        ground_win_times = 0
        if msg.first_ground.self_win:
            ground_win_times += 1
        if msg.second_ground.self_win:
            ground_win_times += 1
        if msg.third_ground.self_win:
            ground_win_times += 1

        got_point = PLUNDER_GOT_POINT[self.mongo_plunder.chars[str(_id)].color].get(ground_win_times, 0)

        if got_point:
            self.mongo_plunder.points += got_point

        if msg.self_win:
            counter.incr()
            self.mongo_plunder.target_char = _id

            drop_official_exp = PLUNDER_GET_OFFICIAL_EXP_WHEN_WIN
            drop_gold = PLUNDER_DEFENSE_FAILURE_GOLD

            resource = Resource(self.char_id, "Plunder")
            standard_drop = resource.add(gold=drop_gold, official_exp=drop_official_exp)
        else:
            self.mongo_plunder.target_char = 0
            standard_drop = make_standard_drop_from_template()

        self.mongo_plunder.got_reward = []
        self.mongo_plunder.save()
        self.send_notify()
        return (msg, standard_drop)


    def get_reward(self, tp):
        if not self.mongo_plunder.target_char:
            raise SanguoException(
                errormsg.PLUNDER_GET_REWARD_NO_TARGET,
                self.char_id,
                "Plunder Get Reward",
                "no Target char"
            )

        if tp in self.mongo_plunder.got_reward:
            raise SanguoException(
                errormsg.PLUNDER_GET_REWARD_ALREADY_GOT,
                self.char_id,
                "Plunder Get Reward",
                "tp {0} already got".format(tp)
            )

        need_points = PLUNDER_REWARD_NEEDS_POINT[tp]
        if self.mongo_plunder.points < need_points:
            raise SanguoException(
                errormsg.PLUNDER_GET_REWARD_POINTS_NOT_ENOUGH,
                self.char_id,
                "Plunder Get Reward",
                "points not enough. {0} < {1}".format(self.mongo_plunder.points, need_points)
            )

        self.mongo_plunder.points -= need_points
        self.mongo_plunder.got_reward.append(tp)
        self.mongo_plunder.save()

        char = Char(self.char_id).mc
        vip_plus = VIP_FUNCTION[char.vip].plunder_addition

        standard_drop = make_standard_drop_from_template()

        def _get_gold():
            max_star_stage = max_star_stage_id(self.char_id)
            if not max_star_stage:
                return 0

            gold = STAGES[max_star_stage].normal_gold
            gold = gold * 400 * random.uniform(1.0, 1.2) * (1+vip_plus/100.0)
            return int(gold)

        plunder_gold = _get_gold()

        got_hero_id = 0
        if tp == PLUNDER_HERO:
            f = Formation(self.mongo_plunder.target_char)
            heros = f.in_formation_hero_original_ids()
            got_hero_id = random.choice([hid for hid in heros if hid])
            p = Prison(self.char_id)
            p.prisoner_add(got_hero_id, plunder_gold/2)

        elif tp == PLUNDER_STUFF:
            stage = Stage(self.mongo_plunder.target_char)
            max_star_stage = stage.stage.max_star_stage
            if not max_star_stage:
                max_star_stage = 1

            drop_ids = [int(i) for i in STAGES[max_star_stage].normal_drop.split(',')]
            drop = get_drop(drop_ids, multi=int(PLUNDER_GOT_ITEMS_HOUR * 3600 * (1+vip_plus/100.0) / 15))
            standard_drop.update(drop)

        elif tp == PLUNDER_GOLD:
            standard_drop['gold'] = plunder_gold

        resource = Resource(self.char_id, "Plunder Reward")
        resource.add(**standard_drop)

        self.send_notify()
        if got_hero_id:
            standard_drop['heros'] = [(got_hero_id, 1)]
        return standard_drop_to_attachment_protomsg(standard_drop)


    def send_notify(self):
        counter = Counter(self.char_id, 'plunder')
        msg = PlunderNotify()
        msg.remained_free_times = counter.remained_value
        msg.points = self.mongo_plunder.points
        publish_to_char(self.char_id, pack_msg(msg))
