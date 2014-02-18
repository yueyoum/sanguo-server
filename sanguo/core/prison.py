# -*- coding: utf-8 -*-
import random

from mongoengine import DoesNotExist
from core.mongoscheme import MongoPrison, MongoEmbededPrisoner
from core.exception import SyceeNotEnough
from core.character import Char
from core.exception import InvalidOperate
from core.hero import save_hero
from preset.settings import MAX_PRISONERS_AMOUNT, PRISON_INCR_AMOUNT_COST
import protomsg
from utils import pack_msg
from core.msgpipe import publish_to_char

class Prison(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.p = MongoPrison.objects.get(id=self.char_id)
        except DoesNotExist:
            self.p = MongoPrison(id=self.char_id, amount=MAX_PRISONERS_AMOUNT)
            self.p.save()

    @property
    def max_prisoner_amount(self):
        return self.p.amount

    def prisoner_full(self):
        return len(self.p.prisoners) >= self.max_prisoner_amount

    def incr_max_prisoner_amount(self):
        # TODO
        pass


    def prisoner_add(self, oid):
        if self.prisoner_full():
            return
        prisoner_ids = [int(i) for i in self.p.prisoners.keys()]

        new_prisoner_id = 1
        while True:
            if new_prisoner_id not in prisoner_ids:
                break
            new_prisoner_id += 1

        # FIXME 初始概率
        prob = 10
        p = MongoEmbededPrisoner()
        p.oid = oid
        p.prob = prob

        self.p.prisoners[str(new_prisoner_id)] = p
        self.p.save()

        msg = protomsg.NewPrisonerNotify()
        p = msg.prisoner.add()
        self._fill_up_prisoner_msg(p, new_prisoner_id, oid, prob)

        publish_to_char(self.char_id, pack_msg(msg))

    def prisoner_incr_prob(self, _id):
        str_id = str(_id)
        if str_id not in self.p.prisoners:
            raise InvalidOperate("Prisoner Incr Prob: Char {0} Try to Incr prob for a NONE exists prisoner {1}".format(self.char_id, _id))

        # TODO 消耗物品。增加多少几率
        self.p.prisoners[str_id].prob += 10
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

        self.p.prisoners.pop(str_id)
        self.p.save()

        msg = protomsg.RemovePrisonerNotify()
        msg.ids.append(_id)
        publish_to_char(self.char_id, pack_msg(msg))

        return got


    def incr_amount(self):
        char = Char(self.char_id)
        cache_char = char.cacheobj
        if cache_char.sycee < PRISON_INCR_AMOUNT_COST:
            raise SyceeNotEnough("Prison Incr Amount: Char {0} sycee not enough".format(self.char_id))

        char.update(sycee=-PRISON_INCR_AMOUNT_COST)
        self.p.amount += 1
        self.p.save()
        self.send_notify()


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
        msg.incr_amount_cost = PRISON_INCR_AMOUNT_COST
        publish_to_char(self.char_id, pack_msg(msg))

    def send_prisoners_notify(self):
        msg = protomsg.PrisonerListNotify()
        for k, v in self.p.prisoners.iteritems():
            p = msg.prisoner.add()
            self._fill_up_prisoner_msg(p, int(k), v.oid, v.prob)

        publish_to_char(self.char_id, pack_msg(msg))
