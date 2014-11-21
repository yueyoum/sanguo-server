# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-11-20'

import random

from mongoengine import DoesNotExist
from core.mongoscheme import MongoHorse, MongoEmbeddedHorse
from core.exception import CounterOverFlow, SanguoException
from core.resource import Resource
from core.msgpipe import publish_to_char
from core.formation import Formation
from core.signals import socket_changed_signal
from core.common import FightPowerMixin

from utils import pack_msg
from utils.functional import id_generator

from preset import errormsg
from preset.data import HORSE, STUFFS

from protomsg import (
    HorseFreeStrengthTimesNotify,
    HorsesNotify,
    HorsesUpdateNotify,
    HorsesAddNotify,
    HorsesRemoveNotify,
    Horse as MsgHorse
)


class HorseStrengthFactory(object):
    X = 5
    Y = 0.54
    Z = 2

    @classmethod
    def normalize(cls, horse_oid, attack, defense, hp):
        h = HORSE[horse_oid]
        attack = int(attack)
        defense = int(defense)
        hp = int(hp)

        if attack < 0:
            attack = 0
        if attack > h.attack_upper_limit:
            attack = h.attack_upper_limit

        if defense < 0:
            defense = 0
        if defense > h.defense_upper_limit:
            defense = h.defense_upper_limit

        if hp < 0:
            hp = 0
        if hp > h.hp_upper_limit:
            hp = h.hp_upper_limit

        return attack, defense, hp

    @classmethod
    def normal_strength(cls):
        add_attack = random.randint(0, cls.X) - cls.Y * cls.X * 2
        add_defense = random.randint(0, cls.X) - cls.Y * cls.X
        add_hp = random.randint(0, cls.X * 5) - cls.Y * cls.X * 5

        return add_attack, add_defense, add_hp

    @classmethod
    def sycee_strength(cls):
        add_attack, add_defense, add_hp = cls.normal_strength()
        add_attack += 2 * cls.Z
        add_defense += cls.Z
        add_hp += 5 * cls.Z

        return add_attack, add_defense, add_hp

    @classmethod
    def strength(cls, horse_oid, old_attack, old_defense, old_hp, using_sycee=False):
        if using_sycee:
            method = cls.sycee_strength
        else:
            method = cls.normal_strength

        add_attack, add_defense, add_hp = method()

        new_attack = old_attack + add_attack
        new_defense = old_defense + add_defense
        new_hp = old_hp + add_hp
        return cls.normalize(horse_oid, new_attack, new_defense, new_hp)


class HorseFreeTimesManager(object):
    __slots__ = ['char_id', 'counter',]
    def __init__(self, char_id):
        from core.counter import Counter
        self.char_id = char_id
        self.counter = Counter(char_id, 'horse_strength_free')

    @property
    def remained_times(self):
        return self.counter.remained_value

    def incr(self, value=1):
        self.counter.incr(value)
        self.send_notify()

    def send_notify(self):
        msg = HorseFreeStrengthTimesNotify()
        msg.times = self.remained_times
        publish_to_char(self.char_id, pack_msg(msg))



class OneHorse(FightPowerMixin):
    __slots__ = ['_id', 'oid', 'attack', 'defense', 'hp']

    def __init__(self, _id, oid, attack, defense, hp):
        self._id = _id
        self.oid = oid
        self.attack, self.defense, self.hp = HorseStrengthFactory.normalize(oid, attack, defense, hp)
        self.crit = HORSE[oid].crit

    def strength(self, using_sycee=False):
        new_attack, new_defense, new_hp = HorseStrengthFactory.strength(
            self.oid, self.attack, self.defense, self.hp, using_sycee=using_sycee
        )

        new_horse = OneHorse(self._id, self.oid, new_attack, new_defense, new_hp)
        if new_horse.power < self.power:
            new_horse = OneHorse(
                self._id,
                self.oid,
                (new_attack - self.attack) / 2,
                (new_defense - self.defense) / 2,
                (new_hp - self.hp) / 2
            )

        return new_horse


    def to_mongo_record(self):
        m = MongoEmbeddedHorse()
        m.oid = self.oid
        m.attack = self.attack
        m.defense = self.defense
        m.hp = self.hp
        return m

    def make_msg(self):
        msg = MsgHorse()
        msg.id = self._id
        msg.oid = self.oid
        msg.attack = self.attack
        msg.defense = self.defense
        msg.hp = self.hp
        msg.power = self.power
        return msg


class Horse(object):
    def __init__(self, char_id):
        self.char_id = char_id

        try:
            self.mongo_horse = MongoHorse.objects.get(id=self.char_id)
        except DoesNotExist:
            self.mongo_horse = MongoHorse(id=self.char_id)
            self.mongo_horse.horses = {}
            self.mongo_horse.strengthed_horse = {}
            self.mongo_horse.save()

    def has_horse(self, horse_id):
        return str(horse_id) in self.mongo_horse.horses

    def add(self, oid):
        assert oid in HORSE

        embedded_horse = MongoEmbeddedHorse()
        embedded_horse.oid = oid
        embedded_horse.attack = 0
        embedded_horse.defense = 0
        embedded_horse.hp = 0

        new_id = id_generator('equipment')[0]

        self.mongo_horse.horses[str(new_id)] = embedded_horse
        self.mongo_horse.save()

        hobj = OneHorse(
            new_id,
            embedded_horse.oid,
            embedded_horse.attack,
            embedded_horse.defense,
            embedded_horse.hp
        )

        msg = HorsesAddNotify()
        msg_h = msg.horses.add()
        msg_h.MergeFrom(hobj.make_msg())
        publish_to_char(self.char_id, pack_msg(msg))

    def remove(self, _id):
        self.mongo_horse.horses.pop(str(_id))
        self.mongo_horse.save()

        msg = HorsesRemoveNotify()
        msg.ids.extend([_id])
        publish_to_char(self.char_id, pack_msg(msg))


    def check_sell(self, horse_id):
        if not self.has_horse(horse_id):
            raise SanguoException(
                errormsg.HORSE_NOT_EXIST,
                self.char_id,
                "Horse Check Sell",
                "horse {0} not exist".format(horse_id)
            )

        f = Formation(self.char_id)
        if f.find_socket_by_horse(horse_id):
            raise SanguoException(
                errormsg.HORSE_CAN_NOT_SELL_IN_FORMATION,
                self.char_id,
                "Horse Check Sell",
                "horse {0} in formation, can not sell".format(horse_id)
            )

    def sell(self, _id):
        self.check_sell(_id)

        h = self.mongo_horse.horses[str(_id)]
        got_gold = HORSE[h.oid].sell_gold

        resource = Resource(self.char_id, "Horse Sell", "sell horse {0}".format(_id))
        resource.add(gold=got_gold)

        self.remove(_id)



    def strength(self, _id, method):
        # method: 1 - free ,2 - gold, 3 - sycee

        try:
            h = self.mongo_horse.horses[str(_id)]
        except KeyError:
            raise SanguoException(
                errormsg.HORSE_NOT_EXIST,
                self.char_id,
                "Horse Strength",
                "horse {0} not exist".format(_id)
            )


        try:
            HorseFreeTimesManager(self.char_id).incr()
        except CounterOverFlow:
            # 已经没有免费次数了
            if method == 1:
                # 但还要免费强化，引发异常
                raise SanguoException(
                    errormsg.HORSE_STRENGTH_NO_FREE_TIMES,
                    self.char_id,
                    "Horse Strength",
                    "strength {0} using free times. but no free times".format(_id)
                )

            # 这个时候就要根据method来确定是否using_sycee和 resource_needs了
            if method == 2:
                using_sycee = False
                resource_needs = {'gold': -HORSE[h.oid].strength_gold_needs}
            else:
                using_sycee = True
                resource_needs = {'sycee': -HORSE[h.oid].strength_sycee_needs}
        else:
            # 还有免费次数，直接按照免费来搞
            using_sycee = False
            resource_needs = {}

        hobj = OneHorse(_id, h.oid, h.attack, h.defense, h.hp)

        if resource_needs:
            resource = Resource(self.char_id, "Horse Strength", "strength {0} with method {1}".format(_id, method))
            with resource.check(**resource_needs):
                new_hobj = hobj.strength(using_sycee)
        else:
            new_hobj = hobj.strength(using_sycee)

        self.mongo_horse.strengthed_horse = {str(_id): new_hobj.to_mongo_record()}
        self.mongo_horse.save()

        return new_hobj

    def strength_confirm(self, cancel=False):
        try:
            _id, h = self.mongo_horse.strengthed_horse.items()[0]
        except IndexError:
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                self.char_id,
                "Horse Strength Confirm",
                "no data for confirm"
            )

        self.mongo_horse.strengthed_horse = {}
        self.mongo_horse.save()

        if not cancel:
            self.mongo_horse.horses[str(_id)] = h
            self.mongo_horse.save()
            self.send_update_notify(_id, h)


    def evolution(self, horse_id, horse_soul_id):
        from core.item import Item

        try:
            h = self.mongo_horse.horses[str(horse_id)]
        except KeyError:
            raise SanguoException(
                errormsg.HORSE_NOT_EXIST,
                self.char_id,
                "Hero Evolution",
                "horse {0} not exist".format(horse_id)
            )

        item = Item(self.char_id)
        if not item.has_stuff(horse_soul_id):
            raise SanguoException(
                errormsg.STUFF_NOT_EXIST,
                self.char_id,
                "Hero Evolution",
                "horse soul {0} not exist".format(horse_soul_id)
            )

        stuff = STUFFS[horse_soul_id]
        if stuff.tp != 4:
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                self.char_id,
                "Hero Evolution",
                "stuff {0} tp {1} != 4".format(horse_soul_id, stuff.tp)
            )

        if stuff.value not in HORSE:
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                self.char_id,
                "Hero Evolution",
                "stuff value not in HORSE".format(stuff.value)
            )

        h.oid = stuff.value
        self.mongo_horse.save()
        self.send_update_notify(horse_id, h)


    def send_update_notify(self, _id, h):
        hobj = OneHorse(int(_id), h.oid, h.attack, h.defense, h.hp)
        msg = HorsesUpdateNotify()
        msg.horse.MergeFrom(hobj.make_msg())
        publish_to_char(self.char_id, pack_msg(msg))

        f = Formation(self.char_id)
        socket = f.find_socket_by_horse(_id)
        if socket:
            socket_changed_signal.send(
                sender=None,
                socket_obj=socket
            )



    def send_notify(self):
        msg = HorsesNotify()
        for k, v in self.mongo_horse.horses.iteritems():
            hobj = OneHorse(int(k), v.oid, v.attack, v.defense, v.hp)
            msg_h = msg.horses.add()
            msg_h.MergeFrom(hobj.make_msg())

        publish_to_char(self.char_id, pack_msg(msg))

