# -*- coding: utf-8 -*-


__author__ = 'Wang Chao'
__date__ = '1/22/14'

import time
import random
import base64
import dill

from mongoscheme import DoesNotExist
from core.character import Char
from core.battle import PlunderBattle
from core.mongoscheme import MongoPlunder, MongoAffairs, MongoPlunderBoard
from core.exception import SanguoException
from core.task import Task
from core.prison import Prison
from core.resource import Resource
from core.attachment import make_standard_drop_from_template, get_drop
from core.achievement import Achievement
from core.formation import Formation
from core.signals import plunder_finished_signal
from core.msgpipe import publish_to_char
from core.msgfactory import create_character_infomation_message

from utils.api import apicall, api_server_list
from utils import pack_msg
from preset.settings import (
    PRISONER_POOL,
    PLUNDER_GOT_GOLD_PARAM_BASE_ADJUST,
    PLUNDER_GET_DROPS_MINUTES,
    PLUNDER_GET_PRISONER_PROB,
    PLUNDER_GET_DROPS_TIMES,
    PLUNDER_DROP_DECREASE_FACTOR,
    PLUNDER_DROP_MIN_FACTOR,
)
from preset import errormsg
from preset.data import VIP_FUNCTION, BATTLES

from protomsg import GetPlunderLeaderboardResponse
from protomsg import Battle as MsgBattle
from protomsg import PlunderNotify
from protomsg import Plunder as MsgPlunder


class PlunderCurrentTimeOut(Exception):
    pass


class PlunderRival(object):
    @classmethod
    def search(cls, city_id, exclude_char_id=None, return_dumps=False):
        affairs = MongoAffairs.objects.filter(hang_city_id=city_id)
        affair_ids = [a.id for a in affairs]

        rival_id = 0
        while affair_ids:
            rival_id = random.choice(affair_ids)
            if rival_id != exclude_char_id:
                break

            affair_ids.remove(rival_id)
            rival_id = 0

        obj = cls(rival_id, city_id)
        if not return_dumps:
            return obj

        return base64.b64encode(dill.dumps(obj))


    @classmethod
    def search_all_servers(cls, city_id, exclude_char_id=None):
        # 跨服掠夺
        # 流程
        # 1. 向HUB取到所有的servers
        # 2. random choice一个 server，并且调用其API，获得目标玩家数据
        # 3. 开打
        # 4. 调用HUB 打完的API
        # 5. HUB收到请求后，根据target_char_id所在的server，并调用其对于API

        servers = api_server_list(data={})
        s = random.choice(servers['data'])
        url = "https://{0}:{1}/api/plunder/search/".format(s['host'], s['port_https'])

        data = {
            'city_id': city_id,
            'exclude_char_id': exclude_char_id,
        }

        res = apicall(data=data, cmd=url)
        target = res['data']
        obj = dill.loads(base64.b64decode(target))
        obj.server_url = "https://{0}:{1}".format(s['host'], s['port_https'])

        return obj


    def __init__(self, char_id, city_id):
        from core.affairs import Affairs
        from core.battle.hero import BattleHero

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

            self.gold = Affairs(self.char_id).get_drop()['gold']
            self.msg_char_information = create_character_infomation_message(self.char_id).SerializeToString()

            battle_heros = []
            for hid in self.formation:
                if hid == 0:
                    battle_heros.append(None)
                else:
                    battle_heros.append(BattleHero(hid))

            self.battle_heros = base64.b64encode(dill.dumps(battle_heros))

        else:
            self.char_id = 0
            self.name = ""
            self.level = 0
            self.power = 0
            self.leader = 0
            self.formation = []
            self.hero_original_ids = []

            self.gold = 0
            self.msg_char_information = ""
            self.battle_heros = base64.b64encode(dill.dumps([None] * 9))


    def get_plunder_gold(self, level):
        level_diff = self.level - level
        if level_diff > 8:
            level_diff = 8
        if level_diff < -8:
            level_diff = -8

        result = level_diff * 0.025 + PLUNDER_GOT_GOLD_PARAM_BASE_ADJUST
        return int(result * self.gold)


    def make_plunder_msg(self, level):
        msg = MsgPlunder()
        msg.char.MergeFromString(self.msg_char_information)
        msg.gold = self.get_plunder_gold(level)
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

        target = PlunderRival.search_all_servers(city_id, exclude_char_id=self.char_id)
        self.mongo_plunder.char_id = target.char_id
        self.mongo_plunder.char_name = target.name
        self.mongo_plunder.char_gold = target.get_plunder_gold(Char(self.char_id).mc.level)
        self.mongo_plunder.char_power = target.power
        self.mongo_plunder.char_leader = target.leader
        self.mongo_plunder.char_formation = target.formation
        self.mongo_plunder.char_hero_original_ids = target.hero_original_ids
        self.mongo_plunder.char_city_id = target.city_id
        self.mongo_plunder.battle_heros = target.battle_heros
        self.mongo_plunder.server_url = target.server_url
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
        self.mongo_plunder.battle_heros = ""
        self.mongo_plunder.server_url = ""
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

        rival_battle_heros = dill.loads(base64.b64decode(self.mongo_plunder.battle_heros))

        msg = MsgBattle()
        pvp = PlunderBattle(
            self.char_id,
            self.mongo_plunder.char_id,
            msg,
            self.mongo_plunder.char_name,
            rival_battle_heros,
        )
        pvp.start()

        t = Task(self.char_id)
        t.trig(3)

        to_char_id = self.mongo_plunder.char_id
        target_server_url = self.mongo_plunder.server_url

        if msg.self_win:
            standard_drop = self._get_plunder_reward(
                self.mongo_plunder.char_city_id,
                self.mongo_plunder.char_gold,
                self.mongo_plunder.char_hero_original_ids
            )

            self.clean_plunder_target()

            achievement = Achievement(self.char_id)
            achievement.trig(12, 1)

            PlunderLeaderboardWeekly.incr(self.char_id)
        else:
            standard_drop = make_standard_drop_from_template()

        self.mongo_plunder.plunder_times += 1
        self.mongo_plunder.save()
        self.send_notify()

        plunder_finished_signal.send(
            sender=None,
            from_char_id=self.char_id,
            from_char_name=Char(self.char_id).mc.name,
            to_char_id=to_char_id,
            from_win=msg.self_win,
            standard_drop=standard_drop,
            target_server_url=target_server_url,
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
            drop_prob = max(
                PLUNDER_GET_DROPS_TIMES - (self.mongo_plunder.plunder_times - 1) * PLUNDER_DROP_DECREASE_FACTOR,
                PLUNDER_GET_DROPS_TIMES * PLUNDER_DROP_MIN_FACTOR
            )

            drop = get_drop(drop_ids, multi=int(drop_prob))
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
        msg.success_times_weekly = PlunderLeaderboardWeekly.get_char_times(self.char_id)
        publish_to_char(self.char_id, pack_msg(msg))


    @staticmethod
    def cron_job():
        MongoPlunder._get_collection().update({}, {'$set': {'plunder_times': 0}}, multi=True)


class PlunderLeaderboardWeekly(object):
    @staticmethod
    def incr(char_id, times=1):
        try:
            board = MongoPlunderBoard.objects.get(id=char_id)
        except DoesNotExist:
            board = MongoPlunderBoard(id=char_id)
            board.times = 0

        board.times += times
        board.save()


    @staticmethod
    def get_leaderboard(length=10):
        boards = MongoPlunderBoard.objects.order_by('-times').limit(length)
        return [(b.id, b.times) for b in boards]


    @staticmethod
    def get_char_times(char_id):
        try:
            board = MongoPlunderBoard.objects.get(id=char_id)
        except DoesNotExist:
            board = MongoPlunderBoard(id=char_id)
            board.times = 0
            board.save()

        return board.times

    @staticmethod
    def clean():
        MongoPlunderBoard.drop_collection()

    @staticmethod
    def make_get_response():
        msg = GetPlunderLeaderboardResponse()
        msg.ret = 0
        for cid, times in PlunderLeaderboardWeekly.get_leaderboard():
            leader = msg.leaders.add()
            leader.char.MergeFrom(create_character_infomation_message(cid))
            leader.times = times
        return msg


    @staticmethod
    def load_from_redis():
        # 仅运行一次，用作将redis中的数据导入mongodb
        # 因为已经清除redis_persistence的配置，所以这里写死，先前的配置是 127.0.0.1:6380
        import redis
        from core.server import server
        REDISKEY = '_plunder_leaderboard_weekly:{0}'.format(server.id)

        r = redis.Redis(host='127.0.0.1', port=6380)
        data = r.zrange(REDISKEY, 0, -1, withscores=True)
        for char_id, times in data:
            char_id = int(char_id)
            times = int(times)

            PlunderLeaderboardWeekly.incr(char_id, times)
