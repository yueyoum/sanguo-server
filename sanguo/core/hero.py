# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '12/30/13'

import ctypes

from core.drives import document_ids
from core.mongoscheme import MongoHero
from core.signals import hero_add_signal, hero_del_signal, hero_changed_signal
from core.formation import Formation
from core.exception import InvalidOperate
from core import DLL

from apps.character.models import Character
from apps.hero.models import Hero as ModelHero
from utils import cache


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
        a = self.attack * 2.5 * (1 + self.crit / 2.0)
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

    def _add_equip_attrs(self):
        # XXX
        from core.item import Equipment
        f = Formation(self.char_id)
        socket = f.find_socket_by_hero(self.id)
        if not socket:
            return

        for x in ['weapon', 'armor', 'jewelry']:
            if socket[x]:
                equip = Equipment(self.char_id, socket[x])
                self.attack += equip.attack
                self.defense += equip.defense
                self.hp += equip.hp

                for k, v in equip.gem_attributes.iteritems():
                    value = getattr(self, k)
                    setattr(self, k, value + v)

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

        # TODO 消耗同名卡
        self.hero.step += 1
        self.hero.save()

        hero_changed_signal.send(
            sender=None,
            hero_id=self.id
        )









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
