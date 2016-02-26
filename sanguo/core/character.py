# -*- coding: utf-8 -*-

import datetime
import arrow
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
    new_purchase_signal,
    SignalHeroWeGo,
)

from core.common import level_up


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
    exp = int(round(exp * 10, -1))
    # 75等级后升级需要10倍经验
    if level >= 75:
        exp *= 10

    return exp


def official_update_exp(level):
    exp = pow(level + 1, 3.2) * 0.2 + (level + 1) * 20
    return int(round(exp, -1))



def char_level_up(current_level, current_exp, add_exp):
    return level_up(current_level, current_exp, add_exp, level_update_exp)


def char_official_up(current_official_exp, current_official, add_official_exp):
    new_official_exp = current_official_exp + add_official_exp
    while True:
        need_exp = official_update_exp(current_official)
        if new_official_exp < need_exp:
            break
        current_official += 1
        new_official_exp -= need_exp

    return new_official_exp, current_official


def get_char_property(char_id, key):
    doc = MongoCharacter._get_collection().find_one(
            {'_id': char_id},
            {key: 1}
    )

    return doc[key]

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


    def update(self, gold=0, sycee=0, exp=0, official_exp=0, purchase_got=0, purchase_actual_got=0, update_settings=None):
        # purchase_got 充值获得元宝
        # purchase_actual_got 充值实际获得元宝
        # 比如 有个 商品 是 充1元，得1元宝，但现在做活动，买一送一，也就是充1元，得2元宝
        # 这里的 purchase_got = 1, purchase_actual_got = 2
        # 用户的 元宝 多2, 但是记录 purchase_got 还是加1
        # VIP 也是用 累加的 purchase_got来计算的

        def get_settings(key):
            if not update_settings:
                return True
            return update_settings.get(key, True)


        opended_funcs = []
        char = MongoCharacter.objects.get(id=self.id)

        signal_go = SignalHeroWeGo()

        if gold:
            char.gold += gold
            signal_go.add(
                char_gold_changed_signal,
                sender=None,
                char_id=self.id,
                now_value=char.gold,
                change_value=gold
            )

        # 这里加上_cost_sycee是因为防止同时出现purchase_actual_got和消费的update
        # 虽然逻辑上不可能，但是代码是可以这样调用的
        # 所以为了清晰，这里加上_cost_sycee表示消费了多少元宝
        _cost_sycee = 0
        _add_sycee = 0
        if sycee < 0:
            _cost_sycee = abs(sycee)
        else:
            _add_sycee = sycee

        if sycee or purchase_actual_got:
            char.sycee += sycee + purchase_actual_got
            signal_go.add(
                char_sycee_changed_signal,
                sender=None,
                char_id=self.id,
                now_value=char.sycee,
                cost_value=_cost_sycee,
                add_value=_add_sycee+purchase_actual_got,
            )

        if not CHARACTER_MAX_LEVEL or char.level < CHARACTER_MAX_LEVEL:
            if exp:
                old_level = char.level
                char.level, char.exp = char_level_up(char.level, char.exp, exp)

                if char.level != old_level:
                    signal_go.add(
                        char_level_up_signal,
                        sender=None,
                        char_id=self.id,
                        new_level=char.level,
                    )

                    opended_funcs = FunctionOpen(self.id).trig_by_char_level(char.level)

        if official_exp:
            old_official_level = char.official
            char.official_exp, char.official = char_official_up(char.official_exp, char.official, official_exp)

            if char.official != old_official_level:

                signal_go.add(
                    char_official_up_signal,
                    sender=None,
                    char_id=self.id,
                    new_official=char.official
                )

        total_purchase_got = char.purchase_got + purchase_got
        char.purchase_got = total_purchase_got
        # VIP
        if get_settings('as_vip_exp'):
            char.vip_exp += purchase_got

        old_vip = char.vip
        new_vip = get_vip_level(char.vip_exp)
        if new_vip > old_vip:
            char.vip = new_vip

            signal_go.add(
                vip_changed_signal,
                sender=None,
                char_id=self.id,
                old_vip=old_vip,
                new_vip=new_vip
            )

        char.save()

        self.send_notify(char=char, opended_funcs=opended_funcs)

        if purchase_got > 0 and get_settings('purchase_notify'):
            signal_go.add(
                new_purchase_signal,
                sender=None,
                char_id=self.id,
                new_got=purchase_got,
                total_got=total_purchase_got
            )

        signal_go.emit()


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
        msg.char.leader = self.leader

        if opended_funcs:
            msg.funcs.extend(opended_funcs)

        publish_to_char(self.id, pack_msg(msg))


def char_initialize(account_id, server_id, char_id, name):
    # print "CHAR INIT", account_id, server_id, char_id, name.encode('utf-8')
    now = arrow.utcnow().format("YYYY-MM-DD HH:mm:ss")
    mc = MongoCharacter(id=char_id)
    mc.account_id = account_id
    mc.server_id = server_id
    mc.name = name
    mc.gold = CHARACTER_INIT['gold']
    mc.sycee = CHARACTER_INIT['sycee']
    mc.create_at = now
    mc.last_login = now
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
    # print "CHAR INIT DONE"


def get_char_ids_by_level_range(min_level, max_level, exclude_char_ids=None):
    chars = MongoCharacter.objects.filter(Q(level__gte=min_level) & Q(level__lte=max_level))
    excluded = exclude_char_ids or []
    return [c.id for c in chars if c.id not in excluded]


def get_char_ids_by_last_login(limit=7):
    date = arrow.utcnow().replace(days=-limit)

    dt = datetime.datetime(
        date.year,
        date.month,
        date.day,
        date.hour,
        date.minute,
        date.second
    )

    chars = MongoCharacter._get_collection().find({'last_login': {'$gte': dt}}, {'_id': 1})
    return [c['_id'] for c in chars]
