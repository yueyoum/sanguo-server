# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/22/14'
import random

from mongoscheme import Q, DoesNotExist

from apps.character.models import Character
from apps.stage.models import Stage as ModelStage
from core.character import Char
from core.battle import PVP
from core.stage import Hang
from core.mongoscheme import MongoHang, MongoEmbededPlunderChar, MongoPlunderList

from core.exception import InvalidOperate, CounterOverFlow, SyceeNotEnough
from core.counter import Counter

from protomsg import Battle as MsgBattle
from preset.settings import PLUNDER_COST_SYCEE

PLUNDER_LEVEL_DIFF = 3

class Plunder(object):
    def __init__(self, char_id):
        self.char_id = char_id


    def get_plunder_list(self):
        """


        @return: [(id, name, gold, power, is_robot), ...]
        @rtype: list
        """
        char = Char(self.char_id)
        char_level = char.cacheobj.level

        choosing_list = MongoHang.objects(Q(char_level__gte=char_level-PLUNDER_LEVEL_DIFF) & Q(char_level__lte=char_level+PLUNDER_LEVEL_DIFF))
        choosing_id_list = [(c.id, c.stage_id) for c in choosing_list]
        choosing_id_dict = dict(choosing_id_list)
        ids = []
        while True:
            if len(ids) >= 20 or not choosing_id_list:
                break

            c = random.choice(choosing_id_list)
            choosing_id_list.remove(c)
            if c[0] not in ids:
                ids.append(c[0])

        random.shuffle(ids)
        ids = ids[:10]

        all_stages = ModelStage.all()
        res = []
        golds = []
        for i in ids:
            char = Char(i)
            gold = all_stages[choosing_id_dict[i]].normal_gold
            golds.append(gold)
            res.append((i, char.cacheobj.name, gold, char.power, False))

        if golds:
            min_gold = min(golds)
        else:
            min_gold = all_stages[1].normal_gold
        robot_ids = []
        robot_amount = 10 - len(ids)

        while len(robot_ids) < robot_amount:
            # 添加机器人
            real_chars = Character.objects.filter(level=char_level)
            for c in real_chars:
                if c.id == self.char_id:
                    continue
                robot_ids.append(c.id)
                if len(robot_ids) >= robot_amount:
                    break

            char_level -= 1
            if char_level == 0:
                break

        res = []
        for i in robot_ids:
            char = Char(i)
            res.append((i, char.cacheobj.name, min_gold, char.power, True))

        mongo_plunder_list = MongoPlunderList(id=self.char_id)
        for _id, _, gold, _, is_robot in res:
            x = MongoEmbededPlunderChar()
            x.gold = gold
            x.is_robot = is_robot
            mongo_plunder_list.chars[str(_id)] = x
        mongo_plunder_list.save()

        return res


    def plunder(self, _id):
        try:
            mongo_plunder_list = MongoPlunderList.objects.get(id=self.char_id)
        except DoesNotExist:
            raise InvalidOperate("Plunder: Char {0} Try to Pluner {1}. But Char has no plunder list".format(self.char_id, _id))

        if str(_id) not in mongo_plunder_list.chars:
            raise InvalidOperate("Plunder: Char {0} Try to Pluner {1} which is not in plunder list".format(self.char_id, _id))

        counter = Counter(self.char_id, 'plunder')
        try:
            counter.incr()
        except CounterOverFlow:
            # 使用元宝
            c = Char(self.char_id)
            cache_char = c.cacheobj
            if cache_char.sycee < PLUNDER_COST_SYCEE:
                raise SyceeNotEnough()

            c.update(sycee=-PLUNDER_COST_SYCEE)

        msg = MsgBattle()
        pvp = PVP(self.char_id, _id, msg)
        pvp.start()

        if not mongo_plunder_list.chars[str(_id)].is_robot:
            char = Char(self.char_id)
            h = Hang(self.char_id)
            h.plundered(char.cacheobj.name, msg.self_win)
        return msg

