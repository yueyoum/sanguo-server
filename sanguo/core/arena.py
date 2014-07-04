# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/22/14'

import random

from mongoengine import DoesNotExist
from core.drives import redis_client_two
from core.server import server
from core.msgpipe import publish_to_char
from core.character import Char
from core.battle import PVP
from core.counter import Counter
from core.mongoscheme import MongoArenaTopRanks, MongoArenaWeek
from core.exception import CounterOverFlow, SanguoException
from core.achievement import Achievement
from core.task import Task
from core.resource import Resource
from preset.settings import ARENA_COST_SYCEE, ARENA_GET_SCORE_WHEN_LOST, ARENA_GET_SCORE_WHEN_WIN
from preset.data import VIP_MAX_LEVEL
from utils import pack_msg
import protomsg
from preset import errormsg


REDIS_DAY_KEY = 'arena:day:{0}'.format(server.id)

class Arena(object):
    def __init__(self, char_id):
        self.char_id = char_id

        try:
            self.mongo_week = MongoArenaWeek.objects.get(id=char_id)
        except DoesNotExist:
            self.mongo_week = MongoArenaWeek(id=char_id)
            self.mongo_week.score = 0
            self.mongo_week.rank = 0
            self.mongo_week.save()


    @property
    def day_score(self):
        score = redis_client_two.zscore(REDIS_DAY_KEY, self.char_id)
        return int(score) if score else 0

    @property
    def day_rank(self):
        rank = redis_client_two.zrevrank(REDIS_DAY_KEY, self.char_id)
        return rank+1 if rank else 0

    @property
    def week_score(self):
        return self.mongo_week.score

    @property
    def week_rank(self):
        return self.mongo_week.rank


    @property
    def remained_free_times(self):
        c = Counter(self.char_id, 'arena')
        return c.remained_value

    @property
    def remained_buy_times(self):
        c = Counter(self.char_id, 'arena_buy')
        return c.remained_value

    def inc_day_score(self, score):
        new_score =redis_client_two.zincry(REDIS_DAY_KEY, self.char_id, score)
        return int(new_score)


    def _fill_up_panel_msg(self, msg, day_score=None):
        msg.week_rank = self.week_rank
        msg.day_rank = self.day_rank
        msg.week_score = self.week_score
        msg.day_score = day_score or self.day_score
        msg.remained_free_times = self.remained_free_times
        msg.remained_sycee_times = self.remained_buy_times
        msg.arena_cost = ARENA_COST_SYCEE

        top_ranks = MongoArenaTopRanks.objects.all()
        for t in top_ranks:
            char = msg.chars.add()
            char.rank = t.id
            char.name = t.name


    def send_notify(self, day_score=None):
        msg = protomsg.ArenaNotify()
        self._fill_up_panel_msg(msg, day_score=day_score)
        publish_to_char(self.char_id, pack_msg(msg))


    def choose_rival(self):
        my_score = self.day_score
        choosing = redis_client_two.zrangebyscore(REDIS_DAY_KEY, my_score, my_score)
        choosing.remove(self.char_id)
        if choosing:
            return int(random.choice(choosing))

        choosing = redis_client_two.zrangebyscore(REDIS_DAY_KEY, my_score+1, '+inf')
        if choosing:
            return int(choosing[0])
        return None

    def battle(self):
        counter = Counter(self.char_id, 'arena')
        rival_id = self.choose_rival()
        if not rival_id:
            raise SanguoException(
                errormsg.ARENA_NO_RIVAL,
                self.char_id,
                "Arena Battle",
                "no rival."
            )

        try:
            # 免费次数
            counter.incr()
        except CounterOverFlow:
            counter = Counter(self.char_id, 'arena_buy')

            try:
                # 花费元宝次数
                counter.incr()
            except CounterOverFlow:
                char = Char(self.char_id).mc
                if char.vip < VIP_MAX_LEVEL:
                    raise SanguoException(
                        errormsg.ARENA_NO_TIMES,
                        self.char_id,
                        "Arena Battle",
                        "arena no times. vip current: {0}, max {1}".format(char.vip, VIP_MAX_LEVEL)
                    )
                raise SanguoException(
                    errormsg.ARENA_NO_TIMES_FINAL,
                    self.char_id,
                    "Arena Battle",
                    "arena no times. vip reach max level {0}".format(VIP_MAX_LEVEL)
                )

            else:
                resource = Resource(self.char_id, "Arena Battle", "battle for no free times")
                resource.check_and_remove(sycee=-ARENA_COST_SYCEE)


        msg = protomsg.Battle()
        b = PVP(self.char_id, rival_id, msg)
        b.start()

        achievement = Achievement(self.char_id)

        if msg.self_win:
            score = ARENA_GET_SCORE_WHEN_WIN
            achievement.trig(11, 1)
        else:
            score = ARENA_GET_SCORE_WHEN_LOST

        new_day_score = self.inc_day_score(score)

        achievement.trig(10, self.day_rank)

        t = Task(self.char_id)
        t.trig(2)

        self.send_notify(day_score=new_day_score)
        return msg
