# -*- coding: utf-8 -*-
import random

__author__ = 'Wang Chao'
__date__ = '1/22/14'

from core.msgpipe import publish_to_char
from utils import pack_msg

from core.battle import PVP
from core.counter import Counter

import protomsg


class Arena(object):
    def __init__(self, char_id):
        self.char_id = char_id


    def send_arena_notify(self):
        # FIXME
        msg = protomsg.ArenaNotify()
        msg.week_rank = 1
        msg.week_score = 2
        msg.day_rank = 3
        msg.day_score = 4
        msg.remained_amount = 5

        nb = [
            (1, 1, 'aaa'),
            (2, 2, 'bbb'),
            (3, 3, 'ccc'),
        ]
        for x in nb:
            n = msg.chars.add()
            n.rank, n.id, n.name = x

        publish_to_char(self.char_id, pack_msg(msg))

    def battle(self):
        counter = Counter(self.char_id, 'arena')
        counter.incr()

        # FIXME
        # fake test
        from apps.character.models import Character

        char_ids = Character.objects.values_list('id', flat=True)
        rival_id = random.choice(char_ids)

        msg = protomsg.Battle()
        b = PVP(self.char_id, rival_id, msg)
        b.start()

        return msg
