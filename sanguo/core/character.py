# -*- coding: utf-8 -*-
from django.db.models import Q

from mongoengine import DoesNotExist

from apps.character.models import Character, CharPropertyLog
from apps.config.models import CharInit
from core.counter import Counter
from core.hero import save_hero, Hero
from core.mongoscheme import MongoHero, MongoChar
from preset.settings import COUNTER
from core.signals import char_updated_signal

from core.formation import Formation
from core.achievement import Achievement

from core.msgpipe import publish_to_char
from utils import pack_msg

import protomsg

COUNTER_KEYS = COUNTER.keys()


class Char(object):
    def __init__(self, char_id=None, **kwargs):
        if not char_id:
            account_id = kwargs['account_id']
            server_id = kwargs['server_id']
            name = kwargs['name']
            char = char_initialize(account_id, server_id, name)
            self.id = char.id
        else:
            self.id = char_id


    def delete(self):
        # WARNING
        # 一般不删除角色
        # FIXME mongoscheme 中的全要删除
        pass


    @property
    def cacheobj(self):
        return Character.cache_obj(self.id)

    # 阵法
    @property
    def formation(self):
        f = Formation(self.id)
        return f.formation.formation

    @property
    def sockets(self):
        f = Formation(self.id)
        c = f.formation.sockets
        return {int(k): v for k, v in c.iteritems()}

    @property
    def hero_oid_list(self):
        # 阵法中英雄按照排列顺序的原始ID列表
        heros_dict = self.heros_dict
        f = Formation(self.id)
        c = f.formation
        res = []
        for f in c.formation:
            if f == 0:
                res.append(0)
                continue

            s = c.sockets[str(f)]
            if not s.hero:
                continue

            res.append(heros_dict[s.hero].oid)
        return res



    # 武将
    @property
    def heros_dict(self):
        heros = MongoHero.objects.filter(char=self.id)
        return {h.id: h for h in heros}

    @property
    def heros(self):
        return [Hero.cache_obj(i) for i in self.heros_dict.keys()]

    def save_hero(self, hero_original_ids, add_notify=True):
        return save_hero(self.id, hero_original_ids, add_notify=add_notify)


    def in_bag_hero_ids(self):
        heros = MongoHero.objects.filter(char=self.id)
        hero_ids = [h.id for h in heros]
        f = Formation(self.id)
        for s in f.formation.sockets.values():
            if s.hero:
                hero_ids.remove(s.hero)
        return hero_ids


    @property
    def power(self):
        f = Formation(self.id)
        hero_ids = f.in_formation_hero_ids()
        p = 0
        for hid in hero_ids:
            if hid == 0:
                continue
            h = Hero.cache_obj(hid)
            p += h.power
        return p


    def update(self, gold=0, sycee=0, exp=0, official_exp=0, des=''):
        char = Character.objects.get(id=self.id)
        char.gold += gold
        char.sycee += sycee

        achievement = Achievement(self.id)

        if exp:
            new_exp = char.exp + exp
            level = char.level
            old_level = char.level
            while True:
                need_exp = char.update_needs_exp(level)
                if new_exp < need_exp:
                    break

                level += 1
                new_exp -= need_exp

            char.exp = new_exp
            char.level = level

            achievement.trig(18, char.level)

            if char.level != old_level:
                char_updated_signal.send(
                    sender=None,
                    char_id=self.id
                )

            des = '{0}. Level {1} to {2}'.format(des, old_level, char.level)

        if official_exp:
            new_official_exp = char.off_exp + official_exp
            official_level = char.official
            old_official_level = char.official
            while True:
                need_exp = char.update_official_needs_exp(official_level)
                if new_official_exp < need_exp:
                    break
                official_level += 1
                new_official_exp -= need_exp

            char.official = official_level
            char.off_exp = new_official_exp

            achievement.trig(19, char.official)

            des = '{0}. Official {1} to {2}'.format(des, old_official_level, char.official)

        char.save()

        # save to CharPropertyLog
        CharPropertyLog.objects.create(
            char_id=self.id,
            gold=gold,
            sycee=sycee,
            exp=exp,
            official_exp=official_exp,
            des=des[:255]
        )

        try:
            mongo_char = MongoChar.objects.get(id=self.id)
        except DoesNotExist:
            mongo_char = MongoChar(id=self.id)

        if gold > 0:
            mongo_char.got_gold += gold
        if gold < 0:
            mongo_char.cost_gold += abs(gold)
        if sycee > 0:
            mongo_char.got_sycee += sycee
        if sycee < 0:
            mongo_char.cost_sycee += abs(sycee)

        mongo_char.save()


        achievement.trig(32, char.gold)
        if sycee < 0:
            achievement.trig(31, abs(sycee))

        self.send_notify()


    def send_notify(self):
        char = self.cacheobj
        msg = protomsg.CharacterNotify()
        msg.char.id = char.id
        msg.char.name = char.name
        msg.char.gold = char.gold
        msg.char.sycee = char.sycee
        msg.char.level = char.level
        msg.char.current_exp = char.exp
        msg.char.next_level_exp = char.update_needs_exp()
        msg.char.official = char.official
        msg.char.official_exp = char.off_exp
        msg.char.next_official_exp = char.update_official_needs_exp()

        msg.char.power = self.power

        publish_to_char(self.id, pack_msg(msg))






def char_initialize(account_id, server_id, name):
    from core.prison import Prison
    from core.item import Item


    init = CharInit.cache_obj()

    char = Character.objects.create(
        account_id=account_id,
        server_id=server_id,
        name=name,
        gold=init.gold,
        sycee=init.sycee,
    )
    char_id = char.id

    Prison(char_id)

    for func_name in COUNTER_KEYS:
        Counter(char_id, func_name)

    init_heros = init.decoded_heros
    init_heros_ids = init_heros.keys()

    item = Item(char_id)
    for k, v in init_heros.iteritems():
        weapon, armor, jewelry = v
        new_ids = []
        if not weapon:
            new_ids.append(0)
        else:
            new_ids.append(item.equip_add(weapon, notify=False))
        if not armor:
            new_ids.append(0)
        else:
            new_ids.append(item.equip_add(armor, notify=False))
        if not jewelry:
            new_ids.append(0)
        else:
            new_ids.append(item.equip_add(jewelry, notify=False))

        init_heros[k] = new_ids

    init_heros_equips = init_heros.values()


    hero_ids = save_hero(char_id, init_heros_ids, add_notify=False)

    f = Formation(char_id)

    hero_ids = [
        hero_ids[0], hero_ids[1], hero_ids[2],
        0, 0, 0,
        0, 0,
    ]
    socket_ids = []
    for index, _id in enumerate(hero_ids):
        try:
            weapon, armor, jewelry = init_heros_equips[index]
        except IndexError:
            weapon, armor, jewelry = 0, 0, 0
        _sid = f.save_socket(hero=_id, weapon=weapon, armor=armor, jewelry=jewelry, send_notify=False)
        socket_ids.append(_sid)

    socket_ids = [
        socket_ids[0], socket_ids[3], socket_ids[6],
        socket_ids[1], socket_ids[4], socket_ids[7],
        socket_ids[2], socket_ids[5], 0,
    ]

    f.save_formation(socket_ids, send_notify=False)

    item.gem_add(init.decoded_gems, send_notify=False)
    item.stuff_add(init.decoded_stuffs, send_notify=False)

    return char


def get_char_ids_by_level_range(server_id, min_level, max_level):
    ids = Character.objects.filter(Q(server_id=server_id) & Q(level__gte=min_level) & Q(level__lte=max_level)).values_list('id', flat=True)
    return list(ids)
