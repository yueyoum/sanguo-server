# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '12/30/13'

from core import GLOBAL
from core.drives import document_ids
from core.mongoscheme import MongoHero
from core.signals import hero_add_signal, hero_del_signal
from core.formation import Formation

from apps.character.models import Character
from apps.hero.models import Hero as ModelHero
from utils import cache


def cal_hero_property(original_id, level):
    """

    @param original_id: hero original id
    @type original_id: int
    @param level: hero level (char level)
    @type level: int
    @return: (attack, defense, hp)
    @rtype: tuple
    """

    obj = ModelHero.all()[original_id]
    attack = 20 + level * obj.attack_growing
    defense = 15 + level * obj.defense_growing
    hp = 45 + level * obj.hp_growing

    return int(attack), int(defense), int(hp)


class FightPowerMixin(object):
    @property
    def power(self):
        a = self.attack * 2.5 * (1 + self.crit / 2.0)
        b = (self.hp + self.defense * 5) * (1 + self.dodge / 2.0)
        return int(a + b)


class Hero(FightPowerMixin):
    def __init__(self, hid):
        hero = MongoHero.objects.get(id=hid)
        char = Character.cache_obj(hero.char)

        self.id = hid
        self.oid = hero.oid
        self.level = char.level
        self.char_id = char.id

        self.attack, self.defense, self.hp = \
            cal_hero_property(self.oid, self.level)

        model_hero = ModelHero.all()[hid]
        self.crit = model_hero.crit
        self.dodge = model_hero.dodge

        self.skill = model_hero.skill

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
        MongoHero(id=_id, char=char_id, oid=hero_original_ids[i]).save()

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
