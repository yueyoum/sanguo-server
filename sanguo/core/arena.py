# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/22/14'

import random

from mongoengine import DoesNotExist
from core.drives import redis_client
from core.server import server
from core.msgpipe import publish_to_char
from core.character import Char
from core.battle import PVP
from core.counter import Counter
from core.mongoscheme import MongoArena, MongoEmbeddedArenaBeatenRecord
from core.exception import CounterOverFlow, SanguoException
from core.achievement import Achievement
from core.task import Task
from core.resource import Resource
from preset.data import VIP_MAX_LEVEL
from utils import pack_msg
from utils.decorate import cache_it
import protomsg
from preset import errormsg

from preset.settings import (
    ARENA_COST_SYCEE,
    ARENA_DEFAULT_SCORE,
    ARENA_CD,
    ARENA_TOP_RANKS_CACHE,
    MAIL_ARENA_BEATEN_TITLE,
    MAIl_ARENA_BEATEN_CONTENT_TEMPLATE
)


REDIS_ARENA_KEY = "arena:{0}".format(server.id)
REDIS_ARENA_BATTLE_CD_KEY = lambda _id: "arena:cd:{0}".format(_id)


def calculate_score(my_score, rival_score, win):
    p = 1.0 / (1 + pow(10, (-(my_score-rival_score)) / 400.0))
    w = 1 if win else 0

    if my_score < 2000:
        k = 30
    elif my_score < 2400:
        k = 130 - my_score / 20.0
    else:
        k = 10

    score = my_score + k * (w - p)
    return int(score)


class Arena(object):
    FUNC_ID = 8
    def __init__(self, char_id):
        self.char_id = char_id

        try:
            self.mongo_arena = MongoArena.objects.get(id=char_id)
        except DoesNotExist:
            self.mongo_arena = MongoArena(id=char_id)
            self.mongo_arena.score = ARENA_DEFAULT_SCORE
            self.mongo_arena.save()

        if not self.score:
            redis_client.zadd(REDIS_ARENA_KEY, self.char_id, self.mongo_arena.score)

    @property
    def score(self):
        score = redis_client.zscore(REDIS_ARENA_KEY, self.char_id)
        return int(score) if score else 0

    @property
    def rank(self):
        rank = redis_client.zrevrank(REDIS_ARENA_KEY, self.char_id)
        return rank+1 if rank is not None else 0


    @property
    def remained_free_times(self):
        c = Counter(self.char_id, 'arena')
        return c.remained_value

    @property
    def remained_buy_times(self):
        c = Counter(self.char_id, 'arena_buy')
        return c.remained_value

    def set_score(self, score):
        redis_client.zadd(REDIS_ARENA_KEY, self.char_id, score)
        self.mongo_arena.score = score
        self.mongo_arena.save()


    @cache_it('_redis_arena_top_cache', ARENA_TOP_RANKS_CACHE)
    def get_top_ranks(self):
        # return [(char_id, score, power, name,  leader), ...]
        top_data = redis_client.zrevrange(REDIS_ARENA_KEY, 0, 2, withscores=True)
        tops = []
        for _id, _score in top_data:
            char = Char(int(_id))
            tops.append( (int(_id), _score, char.power, char.mc.name, char.leader_oid) )

        tops.sort(key=lambda item: (-item[1], -item[2]))
        return tops


    def fill_up_panel_msg(self, msg, score=None):
        msg.score = score or self.score
        msg.rank = self.rank
        msg.remained_free_times = self.remained_free_times
        msg.remained_sycee_times = self.remained_buy_times
        msg.arena_cost = ARENA_COST_SYCEE

        top_ranks = self.get_top_ranks()

        for index, top in enumerate(top_ranks):
            char = msg.chars.add()
            char.rank = index + 1
            char.name = top[3]
            char.leader = top[4]
            char.power = top[2]


    def send_notify(self, score=None):
        msg = protomsg.ArenaNotify()
        self.fill_up_panel_msg(msg, score=score)
        publish_to_char(self.char_id, pack_msg(msg))


    def choose_rival(self):
        my_score = self.score

        def _find(low_score, high_score):
            choosing = redis_client.zrangebyscore(REDIS_ARENA_KEY, low_score, high_score)
            if not choosing:
                return None

            if str(self.char_id) in choosing:
                choosing.remove(str(self.char_id))

            while choosing:
                got = random.choice(choosing)
                # check cd
                if redis_client.ttl(REDIS_ARENA_BATTLE_CD_KEY(got)) > 0:
                    choosing.remove(got)
                    continue

                return int(got)

            return None

        got = _find(int(my_score * 0.95), int(my_score * 1.05))
        if got:
            return got

        got = _find(int(my_score * 0.8), int(my_score * 1.2))
        if got:
            return got

        choosing = redis_client.zrangebyscore(REDIS_ARENA_KEY, int(my_score * 1.2), '+inf')
        if choosing:
            if str(self.char_id) in choosing:
                choosing.remove(str(self.char_id))
            return int(choosing[0])
        return None


    def battle(self):
        rival_id = self.choose_rival()
        if not rival_id:
            raise SanguoException(
                errormsg.ARENA_NO_RIVAL,
                self.char_id,
                "Arena Battle",
                "no rival."
            )

        counter = Counter(self.char_id, 'arena')
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

        # set battle cd
        redis_client.setex(REDIS_ARENA_BATTLE_CD_KEY(rival_id), 1, ARENA_CD)

        msg = protomsg.Battle()
        b = PVP(self.char_id, rival_id, msg)
        b.start()


        if msg.self_win:
            achievement = Achievement(self.char_id)
            achievement.trig(11, 1)

        self_score = self.score
        rival_arena = Arena(rival_id)
        rival_score = rival_arena.score

        new_score = calculate_score(self_score, rival_score, msg.self_win)
        self.set_score(new_score)

        t = Task(self.char_id)
        t.trig(2)

        self.send_notify(score=new_score)

        rival_arena.be_beaten(rival_score, self_score, not msg.self_win, self.char_id)

        return msg


    def be_beaten(self, self_score, rival_score, win, rival_id):
        score = calculate_score(self_score, rival_score, win)
        self.set_score(score)

        rival_name = Char(rival_id).mc.name

        record = MongoEmbeddedArenaBeatenRecord()
        record.name = rival_name
        record.old_score = self_score
        record.new_score = score

        self.mongo_arena.beaten_record.append(record)
        self.mongo_arena.save()


    def login_process(self):
        from core.mail import Mail

        if not self.mongo_arena.beaten_record:
            return

        names = []
        for record in self.mongo_arena.beaten_record:
            if len(names) >= 3:
                names.append(u'等')
                break

            names.append(record.name)

        old_score = self.mongo_arena.beaten_record[0].old_score
        new_score = self.mongo_arena.beaten_record[-1].new_score

        content = MAIl_ARENA_BEATEN_CONTENT_TEMPLATE.format(u','.join(names), old_score, new_score)

        Mail(self.char_id).add(MAIL_ARENA_BEATEN_TITLE, content, send_notify=False)

        self.mongo_arena.beaten_record = []
        self.mongo_arena.save()

