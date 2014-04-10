# -*- coding: utf-8 -*-


__author__ = 'Wang Chao'
__date__ = '1/22/14'
import random
import logging

from django.db import transaction
from mongoscheme import Q, DoesNotExist
from core.character import Char, get_char_ids_by_level_range
from core.battle import PVP
from core.stage import Hang
from core.mongoscheme import MongoHang, MongoPlunder, MongoEmbededPlunderChars, MongoStage
from core.exception import InvalidOperate
from core.counter import Counter
from core.task import Task
from core.formation import Formation
from core.prison import Prison
from core.stage import Stage
from protomsg import Battle as MsgBattle
from protomsg import PlunderNotify
from core.msgpipe import publish_to_char
from utils import pack_msg
from preset.settings import (
    PLUNDER_GET_OFFICIAL_EXP_WHEN_WIN,
    PLUNDER_POINT,
    PLUNDER_DEFENSE_FAILURE_GOLD,
    PLUNDER_REWARD_NEEDS_POINT,
    PLUNDER_GOT_ITEMS_HOUR,
)
from protomsg import PLUNDER_HERO, PLUNDER_STUFF


logger = logging.getLogger('sanguo')

PLUNDER_LEVEL_DIFF = 10

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
        @return: [[id, name, power, formation, is_robot, gold], ...]
        @rtype: list
        """
        char = Char(self.char_id)
        cache_char = char.cacheobj
        char_level = cache_char.level

        choosing_list = MongoHang.objects(Q(char_level__gte=char_level-PLUNDER_LEVEL_DIFF) & Q(char_level__lte=char_level+PLUNDER_LEVEL_DIFF) & Q(id__ne=self.char_id))
        choosing_id_list = [c.id for c in choosing_list]
        ids = []
        while True:
            if len(ids) >= 20 or not choosing_id_list:
                break

            c = random.choice(choosing_id_list)
            choosing_id_list.remove(c)
            if c == self.char_id:
                continue

            if c not in ids:
                ids.append(c)

        random.shuffle(ids)
        ids = ids[:10]

        res = []
        for i in ids:
            char = Char(i)
            f = Formation(i)
            res.append([i, char.cacheobj.name, char.power, f.in_formation_hero_original_ids(), False])

        robot_ids = []
        robot_amount = 10 - len(ids)

        if len(robot_ids) < robot_amount:
            # 添加机器人
            min_level = char_level - 20
            if min_level <= 1:
                min_level = 1
            real_chars = get_char_ids_by_level_range(cache_char.server_id, min_level, char_level + 10)

            for c in real_chars:
                if c == self.char_id:
                    continue

                if c in ids:
                    continue

                robot_ids.append(c)
                if len(robot_ids) >= robot_amount:
                    break

        for i in robot_ids:
            char = Char(i)
            f = Formation(i)
            res.append([i, char.cacheobj.name, char.power, f.in_formation_hero_original_ids(), True])

        final_ids = [r[0] for r in res]
        this_stages = MongoStage.objects.filter(id__in=final_ids)
        this_stages_dict = {s.id: s.max_star_stage for s in this_stages}
        for r in res:
            _id = r[0]
            max_star_stage = this_stages_dict.get(_id, 1)
            if not max_star_stage:
                max_star_stage = 1

            got_gold = max_star_stage * 400 * random.uniform(1.0, 1.2)
            got_gold = int(got_gold)
            r.append(got_gold)

        for _id, _, _, _, is_robot, gold in res:
            c = MongoEmbededPlunderChars()
            c.is_robot = is_robot
            c.gold = gold
            self.mongo_plunder.chars[str(_id)] = c
        self.mongo_plunder.save()
        return res


    def plunder(self, _id):
        if str(_id) not in self.mongo_plunder.chars:
            raise InvalidOperate("Plunder: Char {0} Try to Pluner {1} which is not in plunder list".format(self.char_id, _id))

        counter = Counter(self.char_id, 'plunder')
        if counter.remained_value <= 0:
            raise InvalidOperate("Plunder: Char {0} Try to Plunder {1}. But no times available".format(self.char_id, _id))

        msg = MsgBattle()
        pvp = PVP(self.char_id, _id, msg)
        pvp.start()

        if not self.mongo_plunder.chars[str(_id)].is_robot:
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

        got_point = PLUNDER_POINT.get(ground_win_times, 0)
        if got_point:
            self.mongo_plunder.points += got_point

        if msg.self_win:
            counter.incr()
            self.mongo_plunder.target_char = _id

            drop_official_exp = PLUNDER_GET_OFFICIAL_EXP_WHEN_WIN
            drop_gold = PLUNDER_DEFENSE_FAILURE_GOLD

            char = Char(self.char_id)
            char.update(gold=drop_gold, official_exp=drop_official_exp, des='Plunder Reward')
        else:
            self.mongo_plunder.target_char = 0

        self.mongo_plunder.got_reward = []
        self.mongo_plunder.save()
        self.send_notify()
        return msg


    def get_reward(self, tp):
        if not self.mongo_plunder.target_char:
            raise InvalidOperate("Plunder Get Reward. Char {0} try to get reward type {1}. But no target char".format(self.char_id, tp))

        if tp in self.mongo_plunder.got_reward:
            raise InvalidOperate("Plunder Get Reward. Char {0} try to get tp {1} which has already got".format(self.char_id, tp))

        need_points = PLUNDER_REWARD_NEEDS_POINT[tp]
        if self.mongo_plunder.points < need_points:
            raise InvalidOperate("Plunder Get Reward. Char {0} try to get tp {1}. But points NOT enough. {2} < {3}".format(
                self.char_id, tp, self.mongo_plunder.points, need_points
            ))

        self.mongo_plunder.points -= need_points
        self.mongo_plunder.save()

        got_hero_id = 0
        got_equipments = []
        got_gems = []
        got_stuffs = []
        got_gold = 0

        plunder_gold = self.mongo_plunder.chars[str(self.mongo_plunder.target_char)].gold

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
            _, _, got_equipments, got_gems, got_stuffs = stage.save_drop(max_star_stage, times=PLUNDER_GOT_ITEMS_HOUR * 3600 / 15, only_items=True)
        else:
            got_gold = plunder_gold
            char =Char(self.char_id)
            char.update(gold=got_gold)

        self.send_notify()
        return got_hero_id, got_equipments, got_gems, got_stuffs, got_gold


    def send_notify(self):
        free_count = Counter(self.char_id, 'plunder')
        msg = PlunderNotify()
        msg.remained_free_times = free_count.remained_value
        msg.points = self.mongo_plunder.points
        publish_to_char(self.char_id, pack_msg(msg))
