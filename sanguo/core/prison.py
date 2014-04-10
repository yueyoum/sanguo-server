# -*- coding: utf-8 -*-
import random

from mongoengine import DoesNotExist
from django.db import transaction

from core.mongoscheme import MongoPrison, MongoEmbededPrisoner
from core.exception import SyceeNotEnough
from core.character import Char
from core.exception import InvalidOperate, StuffNotEnough
from core.hero import save_hero
from core.msgpipe import publish_to_char
from core.achievement import Achievement
from core.task import Task
from core.item import Item

from utils import pack_msg

from preset.settings import (
    PRISONER_START_PROB,
    PRISONER_RELEASE_GOT_TREASURE,
    PRISONER_KILL_GOT_TREASURE,
    PRISONER_KILL_GOT_SOUL,
)

import protomsg

from preset.data import HEROS, STUFFS, TREASURES


class Prison(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.p = MongoPrison.objects.get(id=self.char_id)
        except DoesNotExist:
            self.p = MongoPrison(id=self.char_id)
            self.p.save()

    def prisoner_add(self, oid, gold):
        prisoner_ids = [int(i) for i in self.p.prisoners.keys()]

        new_prisoner_id = 1
        while True:
            if new_prisoner_id not in prisoner_ids:
                break
            new_prisoner_id += 1

        p = MongoEmbededPrisoner()
        p.oid = oid
        p.prob = PRISONER_START_PROB
        p.active = True
        p.gold = gold

        self.p.prisoners[str(new_prisoner_id)] = p
        self.p.save()

        msg = protomsg.NewPrisonerNotify()
        msg_p = msg.prisoner.add()
        self._fill_up_prisoner_msg(msg_p, new_prisoner_id, oid, PRISONER_START_PROB, True)

        publish_to_char(self.char_id, pack_msg(msg))


    def prisoner_get(self, _id, treasures):
        str_id = str(_id)
        if str_id not in self.p.prisoners:
            raise InvalidOperate("Prisoner Get: Char {0} Try to get a NONE exist prisoner {1}".format(self.char_id, _id))

        if not self.p.prisoners[str_id].active:
            raise InvalidOperate("Prisoner Get. Char {0} Try to get a NOT active prisoner {1}".format(self.char_id, _id))

        item = Item(self.char_id)
        for tid in treasures:
            if not item.has_stuff(tid, 1):
                raise StuffNotEnough("Prisoner Get. Char {0} get prisoner {1}. Using {2}. But {3} not enough".format(
                    self.char_id, _id, treasures, tid
                ))

        treasures_prob = 0
        for tid in treasures:
            try:
                treasures_prob += TREASURES[tid].value
            except KeyError:
                raise InvalidOperate("Prisoner Get. Char {0} try to get {1}. Using a NONE treasure {2}".format(self.char_id, _id, tid))

        for tid in treasures:
            item.stuff_remove(tid, 1)

        got = False
        prob = self.p.prisoners[str_id].prob + treasures_prob
        if prob >= random.randint(1, 100):
            # got it
            save_hero(self.char_id, self.p.prisoners[str_id].oid)
            got = True
            #
            # achievement = Achievement(self.char_id)
            # achievement.trig(9, 1)

            self.p.prisoners.pop(str_id)

            msg = protomsg.RemovePrisonerNotify()
            msg.ids.append(_id)
            publish_to_char(self.char_id, pack_msg(msg))

        else:
            self.p.prisoners[str_id].active = False

            msg = protomsg.UpdatePrisonerNotify()
            p = msg.prisoner.add()
            p_obj = self.p.prisoners[str_id]
            self._fill_up_prisoner_msg(p, _id, p_obj.oid, p_obj.prob, p_obj.active)

            publish_to_char(self.char_id, pack_msg(msg))

        self.p.save()

        t = Task(self.char_id)
        t.trig(5)

        return got


    def _abandon(self, _id):
        try:
            p = self.p.prisoners.pop(str(_id))
        except KeyError:
            raise InvalidOperate("Prisoner Release. Char {0} Try to release a NONE exists prisoner {1}".format(self.char_id, _id))

        self.p.save()

        msg = protomsg.RemovePrisonerNotify()
        msg.ids.append(_id)
        publish_to_char(self.char_id, pack_msg(msg))
        return p

    def release(self, _id):
        p = self._abandon(_id)
        got_gold = p.gold
        got_treasure = random.choice(PRISONER_RELEASE_GOT_TREASURE[HEROS[p.oid].quality])

        char = Char(self.char_id)
        char.update(gold=got_gold, des="Prisoner Release")

        stuffs = [(got_treasure, 1)]

        item = Item(self.char_id)
        item.stuff_add(stuffs)

        return got_gold, stuffs


    def kill(self, _id):
        p = self._abandon(_id)
        quality = HEROS[p.oid].quality
        souls = [(22, PRISONER_KILL_GOT_SOUL[quality])]

        treasures = [(random.choice(PRISONER_KILL_GOT_TREASURE[quality]), 1)]

        stuffs = []
        stuffs.extend(souls)
        stuffs.extend(treasures)

        item = Item(self.char_id)
        item.stuff_add(stuffs)
        return stuffs


    def _fill_up_prisoner_msg(self, p, _id, oid, prob, active):
        p.id = _id
        p.oid = oid
        p.prob = prob
        p.active = active


    def send_prisoners_notify(self):
        msg = protomsg.PrisonerListNotify()
        for k, v in self.p.prisoners.iteritems():
            p = msg.prisoner.add()
            self._fill_up_prisoner_msg(p, int(k), v.oid, v.prob, v.active)

        publish_to_char(self.char_id, pack_msg(msg))
