# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-3'


from core.battle.battle import Battle
from core.battle.hero import InBattleHero

from core.hero import cal_hero_property

from preset.data import HEROS

from protomsg import Battle as MsgBattle

MY_HEROS = [
    4, 5, 2,
    1, 30, 8,
    28, 0, 56
]

RIVAL_HEROS = [
    13, 12, 15,
    36, 0, 17,
    11, 14, 6
]

class MyHero(InBattleHero):
    HERO_TYPE = 1
    def __init__(self, _id):
        self.id = _id
        self.real_id = _id
        self.original_id = _id
        self.level = 1

        self.attack, self.defense, self.hp = cal_hero_property(_id, 1, 0)
        self.crit = HEROS[_id].crit
        self.dodge = 0
        self.anger = HEROS[_id].anger
        self.default_skill = HEROS[_id].default_skill
        self.skills = [int(i) for i in HEROS[_id].skills.split(',')]

        super(MyHero, self).__init__()


class MyBattle(Battle):
    BATTLE_TYPE = 'PVP'
    def _load_heros(self, hero_ids):
        heros = []
        for hid in hero_ids:
            if not hid:
                heros.append(None)
            else:
                heros.append(MyHero(hid))
        return heros

    def load_my_heros(self, *args):
        return self._load_heros(MY_HEROS)

    def load_rival_heros(self, *args):
        return self._load_heros(RIVAL_HEROS)

    def get_my_name(self, *args):
        return u"曹操军"

    def get_rival_name(self, *args):
        return u"刘备军"


def make_battle():
    msg = MsgBattle()
    b = MyBattle(1, 2, msg)
    b.start()
    return msg

def write_msg(file_name, msg):
    with open(file_name, 'wb') as f:
        f.write(msg.SerializeToString())


if __name__ == '__main__':
    msg = make_battle()
    write_msg('/tmp/battle.bin', msg)

