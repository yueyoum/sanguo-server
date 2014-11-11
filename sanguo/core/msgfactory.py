# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-11-10'

from protomsg import CharacterInfomation

def create_character_infomation_message(char_id):
    from core.character import Char
    from core.formation import Formation
    from core.hero import char_heros_dict

    msg = CharacterInfomation()

    char = Char(char_id)
    heros = char_heros_dict(char_id)
    f = Formation(char_id)

    msg.id = char.mc.id
    msg.name = char.mc.name
    msg.level = char.mc.level
    msg.vip = char.mc.vip
    msg.power = char.power

    msg.leader = f.get_leader_oid()

    for hid in f.in_formation_hero_ids():
        msg_hero = msg.formation.add()
        if hid == 0:
            msg_hero.id = 0
            msg_hero.oid = 0
            msg_hero.step = 0
        else:
            h = heros[hid]
            msg_hero.id = h.id
            msg_hero.oid = h.oid
            msg_hero.step = h.step

    return msg
