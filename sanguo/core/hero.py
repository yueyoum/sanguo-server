# -*- coding: utf-8 -*-

from core import GLOBAL
from core.drives import document_ids
from core.mongoscheme import MongoHero
from core.signals import hero_add_signal, hero_del_signal
from apps.character.cache import get_cache_character


def cal_hero_property(original_id, level):
    attack = 20 + level * GLOBAL.HEROS[original_id]['attack_grow']
    defense = 15 + level * GLOBAL.HEROS[original_id]['defense_grow']
    hp = 45 + level * GLOBAL.HEROS[original_id]['hp_grow']

    return int(attack), int(defense), int(hp)


class FightPowerMixin(object):
    @property
    def power(self):
        a = self.attack * 2.5 * (1 + self.crit / 2.0)
        b = (self.hp + self.defense * 5) * (1 + self.dodge / 2.0)
        return int(a + b)
    



class Hero(FightPowerMixin):
    __slots__ = [
        'id', 'char_id', 'oid',
        'attack', 'defense', 'hp',
        'crit', 'dodge'
    ]
    def __init__(self, hid, oid, level, char_id):
        self.id = hid
        self.oid = oid
        self.level = level
        self.char_id = char_id

        self.attack, self.defense, self.hp = \
                cal_hero_property(self.oid, self.level)

        self.crit = 0
        self.dodge = 0




def save_hero(char_id, hero_original_ids, add_notify=True):
    if not isinstance(hero_original_ids, (list, tuple)):
        hero_original_ids = [hero_original_ids]
    
    length = len(hero_original_ids)
    new_max_id = document_ids.inc('charhero', length)
    
    id_range = range(new_max_id-length+1, new_max_id+1)
    for i, _id in enumerate(id_range):
        MongoHero(id=_id, char=char_id, oid=hero_original_ids[i]).save()

    if add_notify:
        hero_add_signal.send(
            sender = None,
            char_id = char_id,
            hero_ids = id_range
        )
    
    return id_range


def get_hero(_id):
    hero = MongoHero.objects.get(id=_id)
    char_obj = get_cache_character(hero.char)
    return Hero(_id, hero.oid, char_obj.level, char_obj.id)


def delete_hero(char_id, ids):
    # XXX
    # 之能删除背包中的英雄，不能删除在阵法中的。注意！
    for i in ids:
        MongoHero.objects(id=i).delete()

    hero_del_signal.send(
        sender = None,
        char_id = char_id,
        hero_ids = ids
    )
