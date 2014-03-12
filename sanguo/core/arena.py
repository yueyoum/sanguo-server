# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/22/14'

import random
from mongoengine import DoesNotExist

from apps.character.models import Character

from core.msgpipe import publish_to_char
from utils import pack_msg
from core.drives import redis_client_two

from core.character import Char
from core.battle import PVP
from core.counter import Counter
from core.mongoscheme import MongoArenaTopRanks, MongoArena
from core.exception import CounterOverFlow, SyceeNotEnough, InvalidOperate
from core.achievement import Achievement
from core.task import Task
from preset.settings import ARENA_COST_SYCEE, ARENA_GET_SCORE_WHEN_LOST, ARENA_GET_SCORE_WHEN_WIN

import protomsg

REDIS_DAY_KEY = 'arenaday'
REDIS_WEEK_KEY = 'arenaweek'
SCORE_DIFF = 100


class Arena(object):
    def __init__(self, char_id):
        self.char_id = char_id

    @property
    def day_rank(self):
        rank = redis_client_two.zrevrank(REDIS_DAY_KEY, self.char_id)
        if not rank:
            return 1
        return rank + 1

    @property
    def week_rank(self):
        rank = redis_client_two.zrevrank(REDIS_WEEK_KEY, self.char_id)
        if not rank:
            return 1
        return rank + 1

    @property
    def day_score(self):
        score = redis_client_two.zscore(REDIS_DAY_KEY, self.char_id)
        if not score:
            return 0
        return int(score)

    @property
    def week_score(self):
        score = redis_client_two.zscore(REDIS_WEEK_KEY, self.char_id)
        if not score:
            return 0
        return int(score)

    @property
    def remained_free_times(self):
        c = Counter(self.char_id, 'arena')
        return c.remained_value

    @property
    def remained_sycee_times(self):
        c = Counter(self.char_id, 'arena_sycee')
        return c.remained_value


    def _fill_up_panel_msg(self, msg):
        msg.week_rank = self.week_rank
        msg.day_rank = self.day_rank
        msg.week_score = self.week_score
        msg.day_score = self.day_score
        msg.remained_free_times = self.remained_free_times
        msg.remained_sycee_times = self.remained_sycee_times
        msg.arena_cost = ARENA_COST_SYCEE

        top_ranks = MongoArenaTopRanks.objects.all()
        for t in top_ranks:
            char = msg.chars.add()
            char.rank = t.id
            char.name = t.name


    def send_notify(self):
        msg = protomsg.ArenaNotify()
        self._fill_up_panel_msg(msg)
        publish_to_char(self.char_id, pack_msg(msg))



    def battle(self):
        counter = Counter(self.char_id, 'arena')
        try:
            # 免费次数
            counter.incr()
        except CounterOverFlow:
            counter = Counter(self.char_id, 'arena_sycee')
            try:
                # 花费元宝次数
                counter.incr()
            except CounterOverFlow:
                raise InvalidOperate("Arena Battle. Char {0} has no times to battle".format(self.char_id))
            else:
                char = Char(self.char_id)
                cache_char = char.cacheobj
                if cache_char.sycee < ARENA_COST_SYCEE:
                    raise SyceeNotEnough("Arena Battle: Char {0} have no free times, and sycee not enough".format(self.char_id))
                char.update(sycee=-ARENA_COST_SYCEE, des='Arena Battle Cost')

        my_score = self.day_score
        choosings = redis_client_two.zrangebyscore(REDIS_DAY_KEY, my_score, my_score)
        if str(self.char_id) in choosings:
            choosings.remove(str(self.char_id))

        if not choosings:
            choosings = redis_client_two.zrangebyscore(REDIS_DAY_KEY, my_score-SCORE_DIFF, my_score+SCORE_DIFF)
            if str(self.char_id) in choosings:
                choosings.remove(str(self.char_id))

            if not choosings:
                char_count = Character.objects.count()
                id_list = random.sample(range(1, char_count+1), min(char_count, 100))
                choosings = Character.objects.filter(id__in=id_list).values_list('id', flat=True)
                choosings = list(choosings)
                if self.char_id in choosings:
                    choosings.remove(self.char_id)

                if not choosings:
                    choosings = Character.objects.values_list('id', flat=True)
                    choosings = list(choosings)
                    choosings.remove(self.char_id)

        rival_id = int(random.choice(choosings))

        msg = protomsg.Battle()
        b = PVP(self.char_id, rival_id, msg)
        b.start()

        achievement = Achievement(self.char_id)

        try:
            mongo_arena = MongoArena.objects.get(id=self.char_id)
        except DoesNotExist:
            mongo_arena = MongoArena(id=self.char_id)
            mongo_arena.rank = 0
            mongo_arena.continues_win = 0

        if msg.self_win:
            score = ARENA_GET_SCORE_WHEN_WIN
            achievement.trig(7, 1)
            mongo_arena.continues_win += 1
        else:
            score = ARENA_GET_SCORE_WHEN_LOST
            mongo_arena.continues_win = 0

        mongo_arena.save()
        achievement.trig(26, mongo_arena.continues_win)

        if score:
            redis_client_two.zincrby(REDIS_DAY_KEY, self.char_id, score)

        t = Task(self.char_id)
        t.trig(2)

        day_rank = self.day_rank
        if day_rank == 1:
            achievement.trig(25, 1)

        rank_diff = self.day_rank - mongo_arena.rank
        achievement.trig(24, rank_diff)

        self.send_notify()
        return msg
