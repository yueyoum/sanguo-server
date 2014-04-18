# -*- coding: utf-8 -*-


from django.conf import settings

from mongoengine import Q

from core.hero import save_hero, Hero
from core.mongoscheme import MongoHero, MongoCharacter, MongoStage
from core.signals import char_level_up_signal, char_official_up_signal, char_gold_changed_signal, char_sycee_changed_signal
from core.formation import Formation
from core.functionopen import FunctionOpen
from core.msgpipe import publish_to_char


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
        # if not char_id:
        #     account_id = kwargs['account_id']
        #     server_id = kwargs['server_id']
        #     name = kwargs['name']
        #     char = char_initialize(account_id, server_id, name)
        #     self.id = char.id
        # else:
        #     self.id = char_id
        self.id = char_id
        self.mc = MongoCharacter.objects.get(id=char_id)


    def delete(self):
        # WARNING
        # 一般不删除角色
        # FIXME mongoscheme 中的全要删除
        pass


    @property
    def cacheobj(self):
        # FIXME
        # return Character.cache_obj(self.id)
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


    def update(self, gold=0, sycee=0, exp=0, official_exp=0, des=''):
        # char = Character.objects.get(id=self.id)
        # char = self.cacheobj
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

            des = '{0}. Level {1} to {2}'.format(des, old_level, char.level)


        if official_exp:
            old_official_level = char.official
            char.official_exp, char.official = char_official_up(char.official_exp, char.official, official_exp)

            if char.official != old_official_level:
                char_official_up_signal.send(
                    sender=None,
                    char_id=self.id,
                    new_official=char.official
                )

            des = '{0}. Official {1} to {2}'.format(des, old_official_level, char.official)

        char.save()

        # save to CharPropertyLog
        # CharPropertyLog.objects.create(
        #     char_id=self.id,
        #     gold=gold,
        #     sycee=sycee,
        #     exp=exp,
        #     official_exp=official_exp,
        #     des=des[:255]
        # )

        self.send_notify(char=char, opended_funcs=opended_funcs)


    def send_notify(self, char=None, opended_funcs=None):
        if not char:
            char = self.cacheobj
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

        if opended_funcs:
            msg.funcs.extend(opended_funcs)

        publish_to_char(self.id, pack_msg(msg))


# if settings.IS_GUIDE_SERVER:
#     def char_initialize(account_id, server_id, char_id, name):
#         mc = MongoCharacter(id=char_id)
#         mc.account_id = account_id
#         mc.server_id = server_id
#         mc.name = name
#         mc.gold = CHARINIT.gold
#         mc.sycee = CHARINIT.sycee
#         mc.save()
#
#         f = Formation(char_id)
#         socket_ids = []
#         for i in range(3):
#             _sid = f.save_socket(send_notify=False)
#             socket_ids.append(_sid)
#
#         socket_ids = [
#             socket_ids[0], 0, 0,
#             socket_ids[1], 0, 0,
#             socket_ids[2], 0, 0,
#         ]
#         f.save_formation(socket_ids, send_notify=False)
#         print "char_initialize done"
#
# else:
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
    if not settings.IS_GUIDE_SERVER:
        init_heros[CHARINIT.extra_hero] = [0, 0, 0]

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

    hero_ids = save_hero(char_id, init_heros_ids, add_notify=False)

    f = Formation(char_id)

    hero_ids = hero_ids + (4-len(hero_ids)) * [0]


    socket_ids = []
    for index, _id in enumerate(hero_ids):
        try:
            weapon, armor, jewelry = init_heros_equips[index]
        except IndexError:
            weapon, armor, jewelry = 0, 0, 0
        _sid = f.save_socket(hero=_id, weapon=weapon, armor=armor, jewelry=jewelry, send_notify=False)
        socket_ids.append(_sid)


    socket_ids = [
        socket_ids[0], socket_ids[3], 0,
        socket_ids[1], 0, 0,
        socket_ids[2], 0, 0,
    ]

    f.save_formation(socket_ids, send_notify=False)

    if CHARINIT.decoded_gems:
        item.gem_add(CHARINIT.decoded_gems, send_notify=False)
    if CHARINIT.decoded_stuffs:
        item.stuff_add(CHARINIT.decoded_stuffs, send_notify=False)

    # if not settings.IS_GUIDE_SERVER:
    #     ms = MongoStage(id=char_id)
    #     ms.stages['1'] = True
    #     ms.max_star_stage = 1
    #     ms.stage_new = 2
    #     ms.save()



def get_char_ids_by_level_range(server_id, min_level, max_level):
    # ids = Character.objects.filter(Q(server_id=server_id) & Q(level__gte=min_level) & Q(level__lte=max_level)).values_list('id', flat=True)
    # return list(ids)
    chars = MongoCharacter.objects.filter(Q(server_id=server_id) & Q(level__gte=min_level) & Q(level__lte=max_level))
    return [c.id for c in chars]

