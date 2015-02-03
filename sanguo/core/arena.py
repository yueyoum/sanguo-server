# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/22/14'

import random

from mongoengine import DoesNotExist, Q
from core.drives import redis_client
from core.character import Char
from core.battle import PVP
from core.counter import Counter
from core.mongoscheme import MongoArena, MongoEmbeddedArenaBeatenRecord
from core.exception import SanguoException
from core.achievement import Achievement
from core.task import Task
from core.resource import Resource
from core.msgfactory import create_character_infomation_message
from core.msgpipe import publish_to_char
from preset.data import VIP_MAX_LEVEL
from utils.checkers import func_opened
from utils import pack_msg
import protomsg
from preset import errormsg

from preset.settings import (
    ARENA_INITIAL_SCORE,
    ARENA_LOWEST_SCORE,
    ARENA_RANK_LINE,
    ARENA_COST_SYCEE,
    ARENA_CD,
    MAIL_ARENA_BEATEN_TITLE,
    MAIl_ARENA_BEATEN_LOST_TEMPLATE,
    MAIl_ARENA_BEATEN_WIN_TEMPLATE,
)


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



class ArenaScoreManager(object):
    @staticmethod
    def get_init_score():
        # 获得初始积分
        lowest = MongoArena.objects.order_by('score').limit(1)
        if not lowest:
            return ARENA_INITIAL_SCORE

        lowest = lowest[0]
        score = int(lowest.score)
        if score < ARENA_LOWEST_SCORE:
            score = ARENA_LOWEST_SCORE
        return score

    @staticmethod
    def get_all():
        chars = MongoArena.objects.order_by('score')
        return [(c.id, c.score) for c in chars]

    @staticmethod
    def get_all_desc(amount=None):
        if amount is None:
            chars = MongoArena.objects.order_by('-score')
        else:
            chars = MongoArena.objects.order_by('-score').limit(amount)

        return [(c.id, c.score) for c in chars]

    @staticmethod
    def get_char_score(char_id):
        return MongoArena.objects.get(id=char_id).score

    @staticmethod
    def get_char_rank(char_score):
        rank = MongoArena.objects.filter(score__gt=char_score).count()
        return rank + 1

    @staticmethod
    def get_top_ranks(amount=10):
        ranks = MongoArena.objects.order_by('-score').limit(amount)
        return [(r.id, r.score) for r in ranks]

    @staticmethod
    def get_chars_by_score(low_score=None, high_score=None):
        condition = None
        if low_score:
            condition = Q(score__gte=low_score)
        if high_score:
            condition = condition & Q(score__lte=high_score)

        if condition is None:
            chars = MongoArena.objects.all()
        else:
            chars = MongoArena.objects.filter(condition)

        return [c.id for c in chars]


class Arena(object):
    FUNC_ID = 8
    def __init__(self, char_id):
        self.char_id = char_id
        self.initialize()

    def initialize(self):
        if not func_opened(self.char_id, Arena.FUNC_ID):
            self.mongo_arena = None
            return

        try:
            self.mongo_arena = MongoArena.objects.get(id=self.char_id)
        except DoesNotExist:
            self.mongo_arena = MongoArena(id=self.char_id)
            self.mongo_arena.score = ArenaScoreManager.get_init_score()
            self.mongo_arena.save()


    @property
    def score(self):
        return self.mongo_arena.score

    @property
    def rank(self):
        if self.score < ARENA_RANK_LINE:
            return 5000

        return ArenaScoreManager.get_char_rank(self.score)


    @property
    def remained_free_times(self):
        c = Counter(self.char_id, 'arena')
        return c.remained_value

    @property
    def remained_buy_times(self):
        c = Counter(self.char_id, 'arena_buy')
        return c.remained_value

    def set_score(self, score):
        self.mongo_arena.score = score
        self.mongo_arena.save()

    @classmethod
    def get_top_ranks(cls, amount=10):
        return ArenaScoreManager.get_top_ranks(amount=amount)

    def send_notify(self):
        if self.mongo_arena is None:
            return

        msg = protomsg.ArenaNotify()
        msg.score = self.score
        msg.rank = self.rank
        msg.remained_free_times = self.remained_free_times
        msg.remained_sycee_times = self.remained_buy_times
        msg.arena_cost = ARENA_COST_SYCEE

        publish_to_char(self.char_id, pack_msg(msg))

    def make_panel_response(self):
        if self.mongo_arena is None:
            return None

        msg = protomsg.ArenaPanelResponse()
        msg.ret = 0

        top_ranks = self.get_top_ranks()
        for index, data in enumerate(top_ranks):
            rank = index + 1
            _cid, _score = data

            if _score < ARENA_RANK_LINE:
                break

            board = msg.boards.add()
            board.char.MergeFrom(create_character_infomation_message(_cid))
            board.score = _score
            board.rank = rank

        return msg


    def choose_rival(self):
        my_score = self.score

        def _find(low_score, high_score):
            choosing = ArenaScoreManager.get_chars_by_score(low_score=low_score, high_score=high_score)
            if not choosing:
                return None

            if self.char_id in choosing:
                choosing.remove(self.char_id)

            while choosing:
                got = random.choice(choosing)
                # check cd
                if redis_client.ttl(REDIS_ARENA_BATTLE_CD_KEY(got)) > 0:
                    choosing.remove(got)
                    continue

                return got

            return None

        got = _find(int(my_score * 0.95), int(my_score * 1.05))
        if got:
            return got

        got = _find(int(my_score * 0.8), int(my_score * 1.2))
        if got:
            return got

        choosing = ArenaScoreManager.get_chars_by_score(low_score=int(my_score * 1.2), high_score=None)
        if choosing:
            if self.char_id in choosing:
                choosing.remove(self.char_id)
            return choosing[0]
        return None


    def battle(self):
        need_sycee = 0

        counter = Counter(self.char_id, 'arena')
        if counter.remained_value <= 0:
            counter = Counter(self.char_id, 'arena_buy')
            if counter.remained_value <= 0:
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
                need_sycee = ARENA_COST_SYCEE

        rival_id = self.choose_rival()
        if not rival_id:
            raise SanguoException(
                errormsg.ARENA_NO_RIVAL,
                self.char_id,
                "Arena Battle",
                "no rival."
            )

        if need_sycee:
            resource = Resource(self.char_id, "Arena Battle", "battle for no free times")
            resource.check_and_remove(sycee=-need_sycee)

        counter.incr()

        # set battle cd
        redis_client.setex(REDIS_ARENA_BATTLE_CD_KEY(rival_id), 1, ARENA_CD)

        msg = protomsg.Battle()
        b = PVP(self.char_id, rival_id, msg)
        b.start()

        t = Task(self.char_id)
        t.trig(2)

        adding_score = 0
        if msg.self_win:
            achievement = Achievement(self.char_id)
            achievement.trig(11, 1)

            # 只有打赢才设置积分
            self_score = self.score
            rival_arena = Arena(rival_id)
            rival_score = rival_arena.score

            new_score = calculate_score(self_score, rival_score, msg.self_win)
            self.set_score(new_score)
            adding_score = new_score - self_score

            rival_arena.be_beaten(rival_score, self_score, not msg.self_win, self.char_id)

        self.send_notify()
        return msg, adding_score


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

        if not self.mongo_arena or not self.mongo_arena.beaten_record:
            return

        def _make_content(record):
            if record.old_score > record.new_score:
                template = MAIl_ARENA_BEATEN_LOST_TEMPLATE
                # des = '-{0}'.format(abs(record.old_score - record.new_score))
            else:
                template = MAIl_ARENA_BEATEN_WIN_TEMPLATE
                # des = '+{0}'.format(abs(record.old_score - record.new_score))

            # return template.format(record.name, record.old_score, record.new_score, des)
            return template.format(record.name)

        contents = [_make_content(record) for record in self.mongo_arena.beaten_record[-1:-5:-1]]

        content_header = u'共受到{0}次挑战，积分从{1}变成{2}\n'.format(
            len(self.mongo_arena.beaten_record),
            self.mongo_arena.beaten_record[0].old_score,
            self.mongo_arena.beaten_record[-1].new_score,
        )

        content_body = u'\n'.join(contents)

        content = content_header + content_body
        if len(self.mongo_arena.beaten_record) > 4:
            content += u'\n...'

        Mail(self.char_id).add(MAIL_ARENA_BEATEN_TITLE, content, send_notify=False)

        self.mongo_arena.beaten_record = []
        self.mongo_arena.save()

