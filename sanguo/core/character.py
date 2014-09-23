# -*- coding: utf-8 -*-

from mongoengine import Q

from core.hero import save_hero, Hero, HeroSoul
from core.mongoscheme import MongoCharacter
from core.formation import Formation
from core.functionopen import FunctionOpen
from core.vip import get_vip_level
from core.msgpipe import publish_to_char
from core.signals import (
    char_level_up_signal,
    char_official_up_signal,
    char_gold_changed_signal,
    char_sycee_changed_signal,
    vip_changed_signal,
)


from utils import pack_msg

from preset.settings import (
    CHARACTER_INIT,
    CHARACTER_MAX_LEVEL,
    FORMATION_INIT_TABLE,
    FORMATION_INIT_OPENED_SOCKETS,
)

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

    @property
    def leader_oid(self):
        return Formation(self.id).get_leader_oid()


    def update(self, gold=0, sycee=0, exp=0, official_exp=0, purchase_got=0, purchase_actual_got=0):
        # purchase_got 充值获得元宝
        # purchase_actual_got 充值实际获得元宝
        # 比如 有个 商品 是 充1元，得1元宝，但现在做活动，买一送一，也就是充1元，得2元宝
        # 这里的 purchase_got = 1, purchase_actual_got = 2
        # 用户的 元宝 多2, 但是记录 purchase_got 还是加1
        # VIP 也是用 累加的 purchase_got来计算的
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

        if not CHARACTER_MAX_LEVEL or char.level < CHARACTER_MAX_LEVEL:
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
        char.purchase_got = total_purchase_got

        old_vip = char.vip
        new_vip = get_vip_level(total_purchase_got)
        if new_vip > old_vip:
            char.vip = new_vip

            vip_changed_signal.send(
                sender=None,
                char_id=self.id,
                old_vip=old_vip,
                new_vip=new_vip
            )

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
    mc.gold = CHARACTER_INIT['gold']
    mc.sycee = CHARACTER_INIT['sycee']
    mc.save()

    from core.item import Item
    item = Item(char_id)
    # save equipment
    for _id, _amount in CHARACTER_INIT['equipment']:
        for _x in range(_amount):
            item.equip_add(_id, notify=False)
    # save gem
    if CHARACTER_INIT['gem']:
        item.gem_add(CHARACTER_INIT['gem'], send_notify=False)
    # save stuff
    if CHARACTER_INIT['stuff']:
        item.stuff_add(CHARACTER_INIT['stuff'], send_notify=False)
    # save hero
    if CHARACTER_INIT['hero']:
        save_hero(char_id, CHARACTER_INIT['hero'], add_notify=False)
    # save souls:
    if CHARACTER_INIT['souls']:
        s = HeroSoul(char_id)
        s.add_soul(CHARACTER_INIT['souls'])

    # hero in formation!
    in_formaiton_heros = CHARACTER_INIT['hero_in_formation']

    final_in_formation_heros = {}
    for k, v in in_formaiton_heros.iteritems():
        new_ids = []
        for _equip_id in v:
            if not _equip_id:
                new_ids.append(0)
            else:
                new_ids.append(item.equip_add(_equip_id, notify=False))

        final_in_formation_heros[k] = new_ids

    hero_ids = save_hero(char_id, final_in_formation_heros.keys(), add_notify=False).id_range
    hero_new_id_to_oid_table = dict(zip(hero_ids, final_in_formation_heros.keys()))

    hero_oid_socket_id_table = {}
    f = Formation(char_id)

    for hid in hero_ids:
        this_oid = hero_new_id_to_oid_table[hid]
        weapon, armor, jewelry = final_in_formation_heros[this_oid]

        _sid = f.initialize_socket(hero=hid, weapon=weapon, armor=armor, jewelry=jewelry)
        hero_oid_socket_id_table[this_oid] = _sid

    socket_ids = FORMATION_INIT_TABLE[:]
    for index, oid in enumerate(socket_ids):
        if oid:
            socket_ids[index] = hero_oid_socket_id_table[oid]

    if FORMATION_INIT_OPENED_SOCKETS > len(hero_ids):
        for i in range(FORMATION_INIT_OPENED_SOCKETS - len(hero_ids)):
            _sid = f.initialize_socket()
            for index, sid in enumerate(socket_ids):
                if sid == 0:
                    socket_ids[index] = _sid
                    break

    f.save_formation(socket_ids, send_notify=False)


def get_char_ids_by_level_range(min_level, max_level, exclude_char_ids=None):
    chars = MongoCharacter.objects.filter(Q(level__gte=min_level) & Q(level__lte=max_level))
    excluded = exclude_char_ids or []
    return [c.id for c in chars if c.id not in excluded]
