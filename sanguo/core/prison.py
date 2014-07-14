# -*- coding: utf-8 -*-
import random

from mongoengine import DoesNotExist
from core.mongoscheme import MongoPrison, MongoEmbededPrisoner
from core.exception import SanguoException
from core.character import Char
from core.hero import save_hero
from core.msgpipe import publish_to_char
from core.task import Task
from core.resource import Resource
from core.attachment import standard_drop_to_attachment_protomsg
from utils import pack_msg
from preset.settings import (
    PRISONER_START_PROB,
    PRISONER_RELEASE_GOT_TREASURE,
    PRISONER_KILL_GOT_TREASURE,
)
import protomsg
from preset.data import HEROS, TREASURES, VIP_FUNCTION
from preset import errormsg


class Prison(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.p = MongoPrison.objects.get(id=self.char_id)
        except DoesNotExist:
            self.p = MongoPrison(id=self.char_id)
            self.p.save()

    def vip_changed(self, new_vip):
        new_prob = self.prisoner_prob(new_vip)

        changed = False
        for p in self.p.prisoners:
            if not p.active:
                continue

            p.prob = new_prob
            changed = True

        if changed:
            self.p.save()
            self.send_prisoners_notify()


    def prisoner_prob(self, vip=None):
        if vip is None:
            vip = Char(self.char_id).mc.vip

        vip_plus = VIP_FUNCTION[vip].prisoner_get
        return PRISONER_START_PROB + vip_plus



    def prisoner_add(self, oid, gold):
        prisoner_ids = [int(i) for i in self.p.prisoners.keys()]

        new_prisoner_id = 1
        while True:
            if new_prisoner_id not in prisoner_ids:
                break
            new_prisoner_id += 1

        start_prob = self.prisoner_prob()
        p = MongoEmbededPrisoner()
        p.oid = oid
        p.prob = start_prob
        p.active = True
        p.gold = gold

        self.p.prisoners[str(new_prisoner_id)] = p
        self.p.save()

        msg = protomsg.NewPrisonerNotify()
        msg_p = msg.prisoner.add()
        self._fill_up_prisoner_msg(msg_p, new_prisoner_id, oid, start_prob, True)

        publish_to_char(self.char_id, pack_msg(msg))


    def prisoner_get(self, _id, treasures):
        str_id = str(_id)
        if str_id not in self.p.prisoners:
            raise SanguoException(
                errormsg.PRISONER_NOT_EXIST,
                self.char_id,
                "Prisoner Get",
                "{0} not exist".format(_id)
            )

        if not self.p.prisoners[str_id].active:
            raise SanguoException(
                errormsg.PRISONER_NOT_ACTIVE,
                self.char_id,
                "Prisoner Get",
                "{0} not active".format(_id)
            )

        treasures_prob = 0
        for tid in treasures:
            try:
                treasures_prob += TREASURES[tid].value
            except KeyError:
                raise SanguoException(
                    errormsg.STUFF_NOT_EXIST,
                    self.char_id,
                    "Prisoner Get",
                    "treasure {0} not exist".format(tid)
                )

        def _get():
            got = False
            prob = self.p.prisoners[str_id].prob + treasures_prob
            if prob >= random.randint(1, 100):
                # got it
                save_hero(self.char_id, self.p.prisoners[str_id].oid)
                got = True

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
            return got

        using_stuffs = [(tid, 1) for tid in treasures]
        if using_stuffs:
            resource = Resource(self.char_id, "Prisoner Get")
            with resource.check(stuffs=using_stuffs):
                got = _get()
        else:
            got = _get()

        t = Task(self.char_id)
        t.trig(5)

        return got


    def _abandon(self, _id, action=""):
        try:
            p = self.p.prisoners.pop(str(_id))
        except KeyError:
            raise SanguoException(
                errormsg.PRISONER_NOT_EXIST,
                self.char_id,
                action,
                "prisoner {0} not exist".format(_id)
            )

        self.p.save()

        msg = protomsg.RemovePrisonerNotify()
        msg.ids.append(_id)
        publish_to_char(self.char_id, pack_msg(msg))
        return p


    def release(self, _id):
        p = self._abandon(_id, action="Prisoner Release")
        got_gold = p.gold
        got_treasure = random.choice(PRISONER_RELEASE_GOT_TREASURE[HEROS[p.oid].quality])

        resource = Resource(self.char_id, "Prisoner Release")
        standard_drop = resource.add(gold=got_gold, stuffs=[(got_treasure, 1)])
        return standard_drop_to_attachment_protomsg(standard_drop)


    def kill(self, _id):
        p = self._abandon(_id, action="Prisoner Kill")
        quality = HEROS[p.oid].quality
        prob = random.randint(1, 100)
        if prob <= 33:
            soul_amount = 1
        elif prob <= 66:
            soul_amount = 2
        else:
            soul_amount = 3

        souls = [(p.oid, soul_amount)]

        treasures = [(random.choice(PRISONER_KILL_GOT_TREASURE[quality]), 1)]

        resource = Resource(self.char_id, "Prisoner Kill")
        standard_drop = resource.add(stuffs=treasures, souls=souls)
        return standard_drop_to_attachment_protomsg(standard_drop)


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
