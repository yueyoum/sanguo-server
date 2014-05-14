# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/22/14'

import random

from mongoengine import DoesNotExist, Q
from core.msgpipe import publish_to_char
from utils import pack_msg
from core.battle import PVP
from core.counter import Counter
from core.mongoscheme import MongoArenaTopRanks, MongoArena, MongoArenaDay, MongoArenaWeek, MongoCharacter
from core.exception import CounterOverFlow, SanguoException
from core.achievement import Achievement
from core.task import Task
from core.resource import Resource
from preset.settings import ARENA_COST_SYCEE, ARENA_GET_SCORE_WHEN_LOST, ARENA_GET_SCORE_WHEN_WIN, COUNTER
import protomsg
from preset import errormsg


DAY_MAX_SCORE = (COUNTER['arena'] + COUNTER['arena_sycee']) * ARENA_GET_SCORE_WHEN_WIN


class Arena(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.mongo_day = MongoArenaDay.objects.get(id=char_id)
        except DoesNotExist:
            self.mongo_day = MongoArenaDay(id=char_id)
            self.mongo_day.score = 0
            self.mongo_day.save()

        try:
            self.mongo_week = MongoArenaWeek.objects.get(id=char_id)
        except DoesNotExist:
            self.mongo_week = MongoArenaWeek(id=char_id)
            self.mongo_week.score = 0
            self.mongo_week.rank = 0
            self.mongo_week.save()

    @property
    def day_score(self):
        return self.mongo_day.score

    @property
    def week_rank(self):
        return self.mongo_week.rank

    @property
    def week_score(self):
        return self.mongo_week.score

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
        msg.day_rank = 0
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


    def choose_rival(self):
        my_score = self.day_score
        choosing = []

        score_diff = 2
        while True:
            if score_diff >= DAY_MAX_SCORE:
                break

            choosing = MongoArenaDay.objects.filter(Q(score__gte=my_score-score_diff) & Q(score__lte=my_score+score_diff) & Q(id__ne=self.char_id))
            if choosing:
                break

            score_diff += 2

        choosing = [c.id for c in choosing if c.id != self.char_id]

        if not choosing:
            char_count = MongoCharacter.objects.count()
            id_list = random.sample(range(1, char_count+1), min(char_count, 100))
            choosing = MongoCharacter.objects.filter(id__in=id_list)
            choosing = [c.id for c in choosing]
            if self.char_id in choosing:
                choosing.remove(self.char_id)

            if not choosing:
                choosing = MongoCharacter.objects.all()
                choosing = [c.id for c in choosing]
                choosing.remove(self.char_id)

        return random.choice(choosing)


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
                raise SanguoException(
                    errormsg.ARENA_NO_TIMES,
                    self.char_id,
                    "Arena Battle",
                    "arena no times"
                )
            else:
                resource = Resource(self.char_id, "Arena Battle", "battle for no free times")
                resource.check_and_remove(sycee=-ARENA_COST_SYCEE)

        rival_id = self.choose_rival()

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
            achievement.trig(11, 1)
            mongo_arena.continues_win += 1
        else:
            score = ARENA_GET_SCORE_WHEN_LOST
            mongo_arena.continues_win = 0

        mongo_arena.save()


        if score:
            self.mongo_day.score += score
            self.mongo_day.save()

        t = Task(self.char_id)
        t.trig(2)

        self.send_notify()
        return msg
