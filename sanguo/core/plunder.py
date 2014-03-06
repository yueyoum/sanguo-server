# -*- coding: utf-8 -*-


__author__ = 'Wang Chao'
__date__ = '1/22/14'
import random
import logging

from mongoscheme import Q, DoesNotExist

from apps.character.models import Character
from apps.stage.models import Stage as ModelStage
from core.character import Char
from core.battle import PVP
from core.stage import Hang
from core.mongoscheme import MongoHang, MongoEmbededPlunderChar, MongoPlunderList

from core.exception import InvalidOperate, CounterOverFlow, SyceeNotEnough
from core.counter import Counter
from core.achievement import Achievement
from core.task import Task
from core.formation import Formation
from core.hero import Hero
from core.prison import Prison


from protomsg import Battle as MsgBattle
from protomsg import PlunderNotify
from core.msgpipe import publish_to_char
from utils import pack_msg

from preset.settings import PLUNDER_COST_SYCEE, PLUNDER_GET_OFFICIAL_EXP_WHEN_LOST, PLUNDER_GET_OFFICIAL_EXP_WHEN_WIN, PLUNDER_GET_HERO_PROB

logger = logging.getLogger('sanguo')

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
            # 免费次数
            counter.incr()
        except CounterOverFlow:
            # 使用元宝次数
            counter = Counter(self.char_id, 'plunder_sycee')
            try:
                counter.incr()
            except CounterOverFlow:
                raise
            else:
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

        t = Task(self.char_id)
        t.trig(3)

        if msg.self_win:
            drop_official_exp = PLUNDER_GET_OFFICIAL_EXP_WHEN_WIN
            # FIXME drop_gold
            drop_gold = mongo_plunder_list.chars[str(_id)].gold

            char = Char(self.char_id)
            char.update(gold=drop_gold, official_exp=drop_official_exp)

            achievement = Achievement(self.char_id)
            achievement.trig(8, 1)

            drop_hero_id = 0
            if PLUNDER_GET_HERO_PROB >= random.randint(1, 100):
                prison = Prison(self.char_id)
                if prison.prisoner_full():
                    logger.debug("Plunder. Char {0} prison full. NOT drop hero".format(self.char_id))
                else:
                    # 取对方上阵武将原始ID
                    rival_hero_oids = []

                    f = Formation(_id)
                    sockets = f.formation.sockets.values()
                    heros = [s.hero for s in sockets if s.hero]
                    for h in heros:
                        cache_hero = Hero.cache_obj(h)
                        rival_hero_oids.append(cache_hero.oid)

                    drop_hero_id = random.choice(rival_hero_oids)
                    prison.prisoner_add(drop_hero_id)

                logger.debug("Plunder. Char {0} plunder success. Got Hero: {1}".format(
                    self.char_id, drop_hero_id
                ))
        else:
            drop_gold = 0
            drop_official_exp = PLUNDER_GET_OFFICIAL_EXP_WHEN_LOST
            drop_hero_id = 0

        self.send_notify()
        return msg, drop_gold, drop_official_exp, drop_hero_id


    def send_notify(self):
        count = Counter(self.char_id, 'plunder')
        msg = PlunderNotify()
        msg.amount = count.cur_value
        msg.max_amount = count.max_value
        msg.cost_sycee = PLUNDER_COST_SYCEE
        publish_to_char(self.char_id, pack_msg(msg))
