# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '12/30/13'

import ctypes

from mongoengine import DoesNotExist

from core.drives import document_ids
from core.mongoscheme import MongoHero, MongoAchievement, MongoHeroSoul
from core.signals import hero_add_signal, hero_del_signal, hero_changed_signal
from core.formation import Formation
from core.exception import InvalidOperate, GoldNotEnough
from core import DLL
from core.achievement import Achievement

from apps.character.models import Character
from apps.hero.models import Hero as ModelHero
from apps.achievement.models import Achievement as ModelAchievement
from utils import cache

from core.msgpipe import publish_to_char
from utils import pack_msg

import protomsg

def cal_hero_property(original_id, level, step):
    """

    @param original_id: hero original id
    @type original_id: int
    @param level: hero level (char level)
    @type level: int
    @return: (attack, defense, hp)
    @rtype: tuple
    """
    hero = ModelHero.all()[original_id]
    attack = DLL.hero_attack(level, step, ctypes.c_float(hero.attack_growing))
    defense = DLL.hero_defense(level, step, ctypes.c_float(hero.defense_growing))
    hp = DLL.hero_hp(level, step, ctypes.c_float(hero.hp_growing))

    # TODO 这里不应该int， 检查使用此参数的代码
    return int(attack), int(defense), int(hp)


class FightPowerMixin(object):
    @property
    def power(self):
        a = self.attack * 2.5 * (1 + self.crit / 200.0)
        # b = (self.hp + self.defense * 5) * (1 + self.dodge / 2.0)
        b = self.hp + self.defense * 5
        return int(a + b)


class Hero(FightPowerMixin):
    def __init__(self, hid):
        self.hero = MongoHero.objects.get(id=hid)
        char = Character.cache_obj(self.hero.char)

        self.id = hid
        self.oid = self.hero.oid
        self.step = self.hero.step
        self.level = char.level
        self.char_id = char.id

        # FIXME
        self.attack, self.defense, self.hp = \
            cal_hero_property(self.oid, self.level, self.step)

        model_hero = ModelHero.all()[self.oid]
        self.crit = model_hero.crit
        self.dodge = model_hero.dodge

        self.skills = [int(i) for i in model_hero.skills.split(',')]

        self._add_equip_attrs()
        self._add_achievement_buffs()

    def _add_equip_attrs(self):
        # XXX
        from core.item import Equipment
        f = Formation(self.char_id)
        socket = f.find_socket_by_hero(self.id)
        if not socket:
            return

        for x in ['weapon', 'armor', 'jewelry']:
            equip_id = getattr(socket, x)
            if equip_id:
                equip = Equipment(self.char_id, equip_id)
                self.attack += equip.attack
                self.defense += equip.defense
                self.hp += equip.hp

                for k, v in equip.gem_attributes.iteritems():
                    value = getattr(self, k)
                    setattr(self, k, value + v)


    def _add_achievement_buffs(self):
        try:
            mongo_ach = MongoAchievement.objects.get(id=self.char_id)
        except DoesNotExist:
            return

        all_achievements = ModelAchievement.all()
        buffs = {}
        for i in mongo_ach.complete:
            ach = all_achievements[i]
            if not ach.buff_used_for:
                continue

            buffs[ach.buff_used_for] = buffs.get(ach.buff_used_for, 0) + ach.buff_value

        for k, v in buffs.iteritems():
            value = getattr(self, k)
            if k == 'crit':
                new_value = value + v
            else:
                new_value = value * (1 + v / 100.0)

            new_value = int(new_value)
            setattr(self, k, new_value)



    def save_cache(self):
        cache.set('hero:{0}'.format(self.id), self)

    @staticmethod
    def cache_obj(hid):
        h = cache.get('hero:{0}'.format(hid))
        if h:
            return h

        h = Hero(hid)
        h.save_cache()
        return h


    def step_up(self):
        # 升阶
        if self.step >= 5:
            raise InvalidOperate("Hero Step Up: Char {0} Try to up hero {1}. But this hero already at step 5".format(
                self.char_id, self.id
            ))

        # FIXME 消耗同名卡
        hs = HeroSoul(self.char_id)
        this_hero = ModelHero.all()[self.id]
        soul_id = this_hero.soul_id
        if not hs.has_soul(soul_id, 2):
            raise InvalidOperate("Hero Step Up: Char {0} Try to up Hero {1}. But hero soul not enough".format(self.char_id, self.id))

        hs.remove_soul((soul_id, 2))

        # FIXME 花多少金币
        from core.character import Char
        c = Char(self.char_id)
        cache_char = c.cacheobj
        if cache_char.gold < 1000:
            raise GoldNotEnough("Hero Step Up. Char {0} try to up hero {1}. But gold not enough".format(self.char_id, self.id))

        c.update(gold=-1000)

        self.hero.step += 1
        self.hero.save()

        hero_changed_signal.send(
            sender=None,
            hero_id=self.id
        )

        achievement = Achievement(self.char_id)
        achievement.trig(10, 1)

        if self.step == 5:
            achievement.trig(16, 1)



class HeroSoul(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.mongo_hs = MongoHeroSoul.objects.get(id=self.char_id)
        except DoesNotExist:
            self.mongo_hs = MongoHeroSoul(id=self.char_id)
            self.mongo_hs.souls = {}
            self.mongo_hs.save()

    def has_soul(self, _id, amount=1):
        return self.mongo_hs.souls.get(str(_id), 0) >= amount

    def add_soul(self, souls):
        new_souls = []
        update_souls = []
        for _id, amount in souls:
            str_id = str(_id)
            if str_id in self.mongo_hs.souls:
                self.mongo_hs.souls[str_id] += amount
                update_souls.append((_id, self.mongo_hs.souls[str_id]))
            else:
                self.mongo_hs.souls[str_id] = amount
                new_souls.append((_id, amount))

        self.mongo_hs.save()
        if new_souls:
            msg = protomsg.AddHeroSoulNotify()
            for _id, amount in new_souls:
                s = msg.herosouls.add()
                s.id = _id
                s.amount = amount

            publish_to_char(self.char_id, pack_msg(msg))

        if update_souls:
            msg = protomsg.UpdateHeroSoulNotify()
            for _id, amount in update_souls:
                s = msg.herosouls.add()
                s.id = _id
                s.amount = amount

            publish_to_char(self.char_id, pack_msg(msg))


    def remove_soul(self, souls):
        remove_souls = []
        update_souls = []
        for _id, amount in souls:
            if not self.has_soul(_id, amount):
                raise InvalidOperate("HeroSoul Remove. Char {0} Try to remove a NONE EXISTS/NOT ENOUGH soul {1}. amount {2}".format(
                    self.char_id, _id, amount
                ))

        for _id, amount in souls:
            str_id = str(_id)
            self.mongo_hs.souls[str_id] -= amount
            if self.mongo_hs.souls[str_id] <= 0:
                remove_souls.append(_id)
                self.mongo_hs.souls.pop(str_id)
            else:
                update_souls.append((_id, self.mongo_hs.souls[str_id]))

        self.mongo_hs.save()
        if remove_souls:
            msg = protomsg.RemoveHeroSoulNotify()
            msg.ids.extend(remove_souls)

            publish_to_char(self.char_id, pack_msg(msg))

        if update_souls:
            msg = protomsg.UpdateHeroSoulNotify()
            for _id, amount in update_souls:
                s = msg.herosouls.add()
                s.id = _id
                s.amount = amount

            publish_to_char(self.char_id, pack_msg(msg))

    def send_notify(self):
        msg = protomsg.HeroSoulNotify()
        for _id, amount in self.mongo_hs.souls:
            s = msg.herosouls.add()
            s.id = int(_id)
            s.amount = amount

        publish_to_char(self.char_id, pack_msg(msg))


def save_hero(char_id, hero_original_ids, add_notify=True):
    """

    @param char_id: char id
    @type char_id: int
    @param hero_original_ids: hero original ids
    @type hero_original_ids: int | list | tuple
    @param add_notify: whether send add hero notify
    @type add_notify: bool
    @return: hero id range
    @rtype: list
    """
    if not isinstance(hero_original_ids, (list, tuple)):
        hero_original_ids = [hero_original_ids]

    char_heros = MongoHero.objects.filter(char=char_id)
    char_hero_oids = set( [h.oid for h in char_heros] )

    to_soul_hero_ids = []
    for h in hero_original_ids[:]:
        if h in char_hero_oids:
            to_soul_hero_ids.append(h)
            hero_original_ids.remove(h)

    if to_soul_hero_ids:
        all_model_heros = ModelHero.all()
        souls = {}
        for sid in to_soul_hero_ids:
            this_hero = all_model_heros[sid]
            souls[this_hero.soul_id] = souls.get(this_hero.soul_id, 0) + 1

        hs = HeroSoul(char_id)
        hs.add_soul(souls.items())

    if hero_original_ids:
        length = len(hero_original_ids)
        new_max_id = document_ids.inc('charhero', length)

        id_range = range(new_max_id - length + 1, new_max_id + 1)
        for i, _id in enumerate(id_range):
            MongoHero(id=_id, char=char_id, oid=hero_original_ids[i], step=1).save()

        if add_notify:
            hero_add_signal.send(
                sender=None,
                char_id=char_id,
                hero_ids=id_range
            )

        all_heros = ModelHero.all()
        achievement = Achievement(char_id)
        for oid in hero_original_ids:
            achievement.trig(1, oid)

            quality = all_heros[oid].quality
            if quality == 1:
                achievement.trig(2, 1)
            elif quality == 2:
                achievement.trig(3, 1)
            else:
                achievement.trig(4, 1)

        achievement.trig(5, length)

        return id_range




def delete_hero(char_id, ids):
    # XXX
    # 只能删除背包中的英雄，不能删除在阵法中的。注意！
    """

    @param char_id: char id
    @type char_id: int
    @param ids: hero ids
    @type ids: list | tuple
    """
    for i in ids:
        MongoHero.objects(id=i).delete()

    hero_del_signal.send(
        sender=None,
        char_id=char_id,
        hero_ids=ids
    )
