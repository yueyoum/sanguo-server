# -*- coding: utf-8 -*-


__author__ = 'Wang Chao'
__date__ = '1/22/14'

import time
import random

from mongoscheme import DoesNotExist
from core.character import Char
from core.battle import PVPFromRivalCache
from core.mongoscheme import MongoPlunder, MongoAffairs
from core.exception import SanguoException
from core.task import Task
from core.prison import Prison
from core.resource import Resource
from core.attachment import make_standard_drop_from_template, get_drop
from core.achievement import Achievement
from core.formation import Formation
from core.signals import plunder_finished_signal
from protomsg import Battle as MsgBattle
from protomsg import PlunderNotify
from protomsg import Plunder as MsgPlunder
from core.msgpipe import publish_to_char
from utils import pack_msg
from preset.settings import (
    PRISONER_POOL,
    PLUNDER_GOT_GOLD_PARAM_BASE_ADJUST,
    PLUNDER_GET_DROPS_MINUTES,
    PLUNDER_GET_PRISONER_PROB,
)
from preset import errormsg
from preset.data import VIP_FUNCTION, BATTLES


class PlunderCurrentTimeOut(Exception):
    pass


class PlunderRival(object):
    __slots__ = ['char_id', 'name', 'level', 'power', 'leader', 'formation', 'hero_original_ids', 'city_id']

    @classmethod
    def search(cls, city_id, exclude_char_id=None):
        affairs = MongoAffairs.objects.filter(hang_city_id=city_id)
        affair_ids = [a.id for a in affairs]

        rival_id = 0
        while affair_ids:
            rival_id = random.choice(affair_ids)
            if rival_id != exclude_char_id:
                break

            affair_ids.remove(rival_id)
            rival_id = 0

        return cls(rival_id, city_id)

    def __init__(self, char_id, city_id):
        self.city_id = city_id
        if char_id:
            char = Char(char_id)
            self.char_id = char_id
            self.name = char.mc.name
            self.level = char.mc.level
            self.power = char.power
            self.leader = char.leader_oid

            f = Formation(char_id)
            self.formation = f.in_formation_hero_ids()
            self.hero_original_ids = f.in_formation_hero_original_ids()
        else:
            self.char_id = 0
            self.name = ""
            self.level = 0
            self.power = 0
            self.leader = 0
            self.formation = []
            self.hero_original_ids = []

    def get_plunder_gold(self, level):
        from core.affairs import Affairs
        if not self.char_id:
            return 0

        affairs = Affairs(self.char_id)
        ho = affairs.get_hang_obj()
        gold = ho.gold

        level_diff = self.level - level
        if level_diff > 8:
            level_diff = 8
        if level_diff < -8:
            level_diff = -8

        result = level_diff * 0.025 + PLUNDER_GOT_GOLD_PARAM_BASE_ADJUST
        return int(result * gold)


    def make_plunder_msg(self, level):
        msg = MsgPlunder()
        msg.id = self.char_id
        msg.name = self.name
        msg.level = self.level
        msg.gold = self.get_plunder_gold(level)
        msg.power = self.power
        msg.leader = self.leader
        msg.hero_original_ids.extend(self.hero_original_ids)
        return msg

    def __bool__(self):
        return self.char_id != 0
    __nonzero__ = __bool__


class Plunder(object):
    def __init__(self, char_id):
        self.char_id = char_id
        self.load_mongo_record()

    def load_mongo_record(self):
        try:
            self.mongo_plunder = MongoPlunder.objects.get(id=self.char_id)
            self.set_default_value()
        except DoesNotExist:
            self.mongo_plunder = MongoPlunder(id=self.char_id)
            self.mongo_plunder.current_times = self.max_plunder_times()
            self.mongo_plunder.save()


    def set_default_value(self):
        # 后面新增加的fileds需要初始化数值的。 比如 current_times
        data = {
            'current_times': self.max_plunder_times(),
            'current_times_lock': False,
            'char_id': 0,
            'char_name': "",
            'char_gold': 0,
            'char_power': 0,
            'char_leader': 0,
            'char_formation': [],
            'char_hero_original_ids': [],
            'char_city_id': 0
        }

        record = self.mongo_plunder._get_collection().find_one({'_id': self.char_id})
        for k, v in data.iteritems():
            if k not in record:
                setattr(self.mongo_plunder, k, v)

        self.mongo_plunder.save()


    def get_plunder_target(self, city_id):
        """
        @:rtype: PlunderRival
        """

        target = PlunderRival.search(city_id, exclude_char_id=self.char_id)
        self.mongo_plunder.char_id = target.char_id
        self.mongo_plunder.char_name = target.name
        self.mongo_plunder.char_gold = target.get_plunder_gold(Char(self.char_id).mc.level)
        self.mongo_plunder.char_power = target.power
        self.mongo_plunder.char_leader = target.leader
        self.mongo_plunder.char_formation = target.formation
        self.mongo_plunder.char_hero_original_ids = target.hero_original_ids
        self.mongo_plunder.char_city_id = target.city_id
        self.mongo_plunder.save()

        if target:
            gold_needs = BATTLES[city_id].refresh_cost_gold
            resource = Resource(self.char_id, "Plunder Refresh")
            resource.check_and_remove(gold=-gold_needs)

        return target

    def max_plunder_times(self):
        char = Char(self.char_id)
        return VIP_FUNCTION[char.mc.vip].plunder


    def clean_plunder_target(self):
        self.mongo_plunder.char_id = 0
        self.mongo_plunder.char_name = ""
        self.mongo_plunder.char_gold = 0
        self.mongo_plunder.char_power = 0
        self.mongo_plunder.char_leader = 0
        self.mongo_plunder.char_formation = []
        self.mongo_plunder.char_hero_original_ids = []
        self.mongo_plunder.char_city_id = 0
        self.mongo_plunder.save()


    def change_current_plunder_times(self, change_value, allow_overflow=False):
        max_times = self.max_plunder_times()
        if change_value > 0 and not allow_overflow and self.mongo_plunder.current_times > max_times:
            return

        for i in range(10):
            self.load_mongo_record()
            if not self.mongo_plunder.current_times_lock:
                self.mongo_plunder.current_times_lock = True
                self.mongo_plunder.save()
                break
            else:
                time.sleep(0.2)
        else:
            raise PlunderCurrentTimeOut()

        try:
            self.mongo_plunder.current_times += change_value
            if self.mongo_plunder.current_times < 0:
                self.mongo_plunder.current_times = 0

            if not allow_overflow and change_value > 0:
                max_times = self.max_plunder_times()
                if self.mongo_plunder.current_times > max_times:
                    self.mongo_plunder.current_times = max_times
        finally:
            self.mongo_plunder.current_times_lock = False
            self.mongo_plunder.save()
            self.send_notify()


    def plunder(self):
        if not self.mongo_plunder.char_id:
            raise SanguoException(
                errormsg.PLUNDER_NO_RIVAL,
                self.char_id,
                "Plunder Battle",
                "no rival target"
            )

        if self.mongo_plunder.current_times <= 0:
            raise SanguoException(
                errormsg.PLUNDER_NO_TIMES,
                self.char_id,
                "Plunder Battle",
                "no times"
            )

        self.change_current_plunder_times(change_value=-1)


        msg = MsgBattle()
        pvp = PVPFromRivalCache(
            self.char_id,
            self.mongo_plunder.char_id,
            msg,
            self.mongo_plunder.char_name,
            self.mongo_plunder.char_formation
        )
        pvp.start()

        t = Task(self.char_id)
        t.trig(3)

        to_char_id = self.mongo_plunder.char_id

        if msg.self_win:
            standard_drop = self._get_plunder_reward(
                self.mongo_plunder.char_city_id,
                self.mongo_plunder.char_gold,
                self.mongo_plunder.char_hero_original_ids
            )

            self.clean_plunder_target()

            achievement = Achievement(self.char_id)
            achievement.trig(12, 1)
        else:
            standard_drop = make_standard_drop_from_template()

        self.mongo_plunder.save()
        self.send_notify()

        plunder_finished_signal.send(
            sender=None,
            from_char_id=self.char_id,
            to_char_id=to_char_id,
            from_win=msg.self_win,
            standard_drop=standard_drop
        )

        return (msg, standard_drop)


    def _get_plunder_reward(self, city_id, gold, hero_original_ids):
        def _get_prisoner():
            prison = 0
            heros = [hid for hid in hero_original_ids if hid]

            while heros:
                hid = random.choice(heros)
                heros.remove(hid)
                if hid in PRISONER_POOL:
                    prison = hid
                    break

            if random.randint(1, 100) <= PLUNDER_GET_PRISONER_PROB:
                return prison
            return 0

        char = Char(self.char_id).mc
        vip_plus = VIP_FUNCTION[char.vip].plunder_addition

        standard_drop = make_standard_drop_from_template()
        standard_drop['gold'] = int(gold * (1 + vip_plus / 100.0))

        # 战俘
        got_hero_id = _get_prisoner()
        if got_hero_id:
            p = Prison(self.char_id)
            p.prisoner_add(got_hero_id, gold/2)

            achievement = Achievement(self.char_id)
            achievement.trig(13, 1)

        # 掉落
        city = BATTLES[city_id]
        if city.normal_drop:
            drop_ids = [int(i) for i in city.normal_drop.split(',')]
            drop = get_drop(drop_ids, multi=int(4 * PLUNDER_GET_DROPS_MINUTES * 60 / 15))
            drop.pop('gold')
            standard_drop.update(drop)

        resource = Resource(self.char_id, "Plunder Reward")
        resource.add(**standard_drop)

        self.send_notify()
        if got_hero_id:
            standard_drop['heros'] = [(got_hero_id, 1)]

        return standard_drop


    def send_notify(self):
        self.load_mongo_record()
        msg = PlunderNotify()
        msg.current_times = self.mongo_plunder.current_times
        msg.max_times = self.max_plunder_times()
        publish_to_char(self.char_id, pack_msg(msg))
