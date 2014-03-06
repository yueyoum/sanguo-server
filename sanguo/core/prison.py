# -*- coding: utf-8 -*-
import random

from mongoengine import DoesNotExist

from apps.hero.models import Hero as ModelHero
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

from preset.settings import MAX_PRISONERS_AMOUNT, PRISON_INCR_AMOUNT_COST, PRISON_INCR_MAX_AMOUNT, PRISONER_INCR_PROB, PRISONER_START_PROB

import protomsg


class Prison(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.p = MongoPrison.objects.get(id=self.char_id)
        except DoesNotExist:
            self.p = MongoPrison(id=self.char_id, amount=0)
            self.p.save()

    @property
    def max_prisoner_amount(self):
        return self.p.amount + MAX_PRISONERS_AMOUNT

    def prisoner_full(self):
        return len(self.p.prisoners) >= self.max_prisoner_amount

    def incr_max_prisoner_amount_cost_sycee(self):
        if self.p.amount >= PRISON_INCR_MAX_AMOUNT:
            return 0
        return PRISON_INCR_AMOUNT_COST[self.max_prisoner_amount]

    def incr_max_prisoner_amount(self):
        if self.p.amount >= PRISON_INCR_MAX_AMOUNT:
            raise InvalidOperate("Prison Incr Prisoners Amount. Char {0} amount {1} already touch PRISON_INCR_MAX_AMOUNT {2}".format(
                self.char_id, self.p.amount, PRISON_INCR_MAX_AMOUNT
            ))

        cost = self.incr_max_prisoner_amount_cost_sycee()
        char = Char(self.char_id)
        if char.cacheobj.sycee < cost:
            raise SyceeNotEnough("Prison Incr Prisoners Amount. Char {0} sycee NOT enough".format(self.char_id))

        char.update(sycee=-cost)
        self.p.amount += 1
        self.p.save()
        self.send_notify()



    def prisoner_add(self, oid):
        if self.prisoner_full():
            return
        prisoner_ids = [int(i) for i in self.p.prisoners.keys()]

        new_prisoner_id = 1
        while True:
            if new_prisoner_id not in prisoner_ids:
                break
            new_prisoner_id += 1

        p = MongoEmbededPrisoner()
        p.oid = oid
        p.prob = PRISONER_START_PROB

        self.p.prisoners[str(new_prisoner_id)] = p
        self.p.save()

        msg = protomsg.NewPrisonerNotify()
        p = msg.prisoner.add()
        self._fill_up_prisoner_msg(p, new_prisoner_id, oid, PRISONER_START_PROB)

        publish_to_char(self.char_id, pack_msg(msg))

    def prisoner_incr_prob(self, _id):
        str_id = str(_id)
        if str_id not in self.p.prisoners:
            raise InvalidOperate("Prisoner Incr Prob: Char {0} Try to Incr prob for a NONE exists prisoner {1}".format(self.char_id, _id))

        # TODO 消耗物品。增加多少几率
        item = Item(self.char_id)
        if not item.has_stuff(22, 1):
            raise StuffNotEnough("Prison Prisoner Get. Char {0} Try to get {1}. But Stuff not enough".format(self.char_id, _id))

        item.stuff_remove(22, 1)

        prisoner_oid = self.p.prisoners[str_id].oid
        prisoner_quality = ModelHero.all()[prisoner_oid].quality

        self.p.prisoners[str_id].prob += PRISONER_INCR_PROB[prisoner_quality]
        if self.p.prisoners[str_id].prob > 100:
            self.p.prisoners[str_id].prob = 100
        self.p.save()

        msg = protomsg.UpdatePrisonerNotify()
        p = msg.prisoner.add()
        self._fill_up_prisoner_msg(p, _id, self.p.prisoners[str_id].oid, self.p.prisoners[str_id].prob)
        publish_to_char(self.char_id, pack_msg(msg))


    def prisoner_get(self, _id):
        str_id = str(_id)
        if str_id not in self.p.prisoners:
            raise InvalidOperate("Prisoner Get: Char {0} Try to get a NONE exist prisoner {1}".format(self.char_id, _id))

        got = False
        prob = self.p.prisoners[str_id].prob
        if prob >= random.randint(1, 100):
            # got it
            save_hero(self.char_id, self.p.prisoners[str_id].oid)
            got = True

            achievement = Achievement(self.char_id)
            achievement.trig(9, 1)

        self.p.prisoners.pop(str_id)
        self.p.save()

        t = Task(self.char_id)
        t.trig(5)

        msg = protomsg.RemovePrisonerNotify()
        msg.ids.append(_id)
        publish_to_char(self.char_id, pack_msg(msg))

        return got


    def _fill_up_prisoner_msg(self, p, _id, oid, prob):
        p.id = _id
        p.oid = oid
        p.prob = prob

        # FIXME
        p.attack = 0
        p.defense = 0
        p.hp = 0
        p.crit = 0


    def send_notify(self):
        msg = protomsg.PrisonNotify()
        msg.max_prisoners_amount = self.max_prisoner_amount
        msg.incr_amount_cost = self.incr_max_prisoner_amount_cost_sycee()
        publish_to_char(self.char_id, pack_msg(msg))

    def send_prisoners_notify(self):
        msg = protomsg.PrisonerListNotify()
        for k, v in self.p.prisoners.iteritems():
            p = msg.prisoner.add()
            self._fill_up_prisoner_msg(p, int(k), v.oid, v.prob)

        publish_to_char(self.char_id, pack_msg(msg))
