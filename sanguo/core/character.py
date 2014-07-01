# -*- coding: utf-8 -*-


from django.conf import settings

from mongoengine import Q

from core.hero import save_hero, Hero
from core.mongoscheme import MongoHero, MongoCharacter, MongoStage
from core.signals import char_level_up_signal, char_official_up_signal, char_gold_changed_signal, char_sycee_changed_signal
from core.formation import Formation
from core.functionopen import FunctionOpen
from core.vip import get_vip_level
from core.msgpipe import publish_to_char
from core.server import server


from utils import pack_msg

from preset.data import CHARINIT

import protomsg


def level_update_exp(level):
    exp = pow(level, 2.5) + level * 20
    return int(round(exp * 10, -1))


def official_update_exp(level):
    exp = pow(level + 1, 3.2) * 0.2 + (level + 1) * 20
    return int(round(exp, -1))



def char_level_up(current_exp, current_level, add_exp):
    new_exp = current_exp + add_exp
    while True:
        need_exp = level_update_exp(current_level)
        if new_exp < need_exp:
            break

        current_level += 1
        new_exp -= need_exp

    return new_exp, current_level

def char_official_up(current_official_exp, current_official, add_official_exp):
    new_official_exp = current_official_exp + add_official_exp
    while True:
        need_exp = official_update_exp(current_official)
        if new_official_exp < need_exp:
            break
        current_official += 1
        new_official_exp -= need_exp

    return new_official_exp, current_official




class Char(object):
    def __init__(self, char_id):
        self.id = char_id
        self.mc = MongoCharacter.objects.get(id=char_id)

    @property
    def cacheobj(self):
        return self.mc


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

    @property
    def leader(self):
        f = Formation(self.id)
        return f.get_leader_id()


    def update(self, gold=0, sycee=0, exp=0, official_exp=0, purchase_got=0, purchase_actual_got=0):
        opended_funcs = []
        char = MongoCharacter.objects.get(id=self.id)
        if gold:
            char.gold += gold
            char_gold_changed_signal.send(
                sender=None,
                char_id=self.id,
                now_value=char.gold,
                change_value=gold
            )

        sycee += purchase_actual_got
        if sycee:
            char.sycee += sycee
            char_sycee_changed_signal.send(
                sender=None,
                char_id=self.id,
                now_value=char.sycee,
                change_value=sycee
            )

        if exp:
            old_level = char.level
            char.exp, char.level = char_level_up(char.exp, char.level, exp)

            if char.level != old_level:
                char_level_up_signal.send(
                    sender=None,
                    char_id=self.id,
                    new_level=char.level,
                )
                opended_funcs = FunctionOpen(self.id).trig_by_char_level(char.level)

        if official_exp:
            old_official_level = char.official
            char.official_exp, char.official = char_official_up(char.official_exp, char.official, official_exp)

            if char.official != old_official_level:
                char_official_up_signal.send(
                    sender=None,
                    char_id=self.id,
                    new_official=char.official
                )

        # VIP
        total_purchase_got = char.purchase_got + purchase_got
        vip = get_vip_level(total_purchase_got)
        char.purchase_got = total_purchase_got
        char.vip = vip

        char.save()
        self.send_notify(char=char, opended_funcs=opended_funcs)


    def send_notify(self, char=None, opended_funcs=None):
        if not char:
            char = self.mc

        msg = protomsg.CharacterNotify()
        msg.char.id = char.id
        msg.char.name = char.name
        msg.char.gold = char.gold
        msg.char.sycee = char.sycee
        msg.char.level = char.level
        msg.char.current_exp = char.exp
        msg.char.next_level_exp = level_update_exp(char.level)
        msg.char.official = char.official
        msg.char.official_exp = char.official_exp
        msg.char.next_official_exp = official_update_exp(char.level)

        msg.char.power = self.power
        msg.char.vip = char.vip
        msg.char.purchase_got = char.purchase_got

        msg.char.leader = self.leader

        if opended_funcs:
            msg.funcs.extend(opended_funcs)

        publish_to_char(self.id, pack_msg(msg))


def char_initialize(account_id, server_id, char_id, name):
    mc = MongoCharacter(id=char_id)
    mc.account_id = account_id
    mc.server_id = server_id
    mc.name = name
    mc.gold = CHARINIT.gold
    mc.sycee = CHARINIT.sycee
    mc.save()

    from core.item import Item

    init_heros = CHARINIT.decoded_heros

    init_heros_ids = init_heros.keys()

    transformed_init_heros = {}

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

        transformed_init_heros[k] = new_ids

    init_heros_equips = transformed_init_heros.values()

    hero_ids = save_hero(char_id, init_heros_ids, add_notify=False).id_range

    f = Formation(char_id)

    hero_ids = hero_ids + (4-len(hero_ids)) * [0]


    socket_ids = []
    for index, _id in enumerate(hero_ids):
        try:
            weapon, armor, jewelry = init_heros_equips[index]
        except IndexError:
            weapon, armor, jewelry = 0, 0, 0
        _sid = f.initialize_socket(hero=_id, weapon=weapon, armor=armor, jewelry=jewelry)
        socket_ids.append(_sid)

    socket_ids = [
        socket_ids[3], socket_ids[0], 0,
        0, socket_ids[1], 0,
        0, socket_ids[2], 0
    ]

    f.save_formation(socket_ids, send_notify=False)

    if CHARINIT.decoded_gems:
        item.gem_add(CHARINIT.decoded_gems, send_notify=False)
    if CHARINIT.decoded_stuffs:
        item.stuff_add(CHARINIT.decoded_stuffs, send_notify=False)


def get_char_ids_by_level_range(min_level, max_level, exclude_char_ids=None, server_id=None):
    server_id = server_id or server.id
    chars = MongoCharacter.objects.filter(Q(server_id=server_id) & Q(level__gte=min_level) & Q(level__lte=max_level))
    excluded = exclude_char_ids or []
    return [c.id for c in chars if c.id not in excluded]
