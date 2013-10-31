from apps.character.models import CharHero
from core import GLOBAL


def cal_hero_property(original_id, level):
    attack = 20 + level * (5 + GLOBAL.HEROS[original_id]['attack_grow'])
    defense = 15 + level * (4 + GLOBAL.HEROS[original_id]['defense_grow'])
    hp = 45 + level * (14 + GLOBAL.HEROS[original_id]['hp_grow'])

    return attack, defense, hp



class Hero(object):
    def __init__(self, charhero_obj):
        self.hero = charhero_obj

        self.id = self.hero.id
        self.original_id = self.hero.hero_id
        self.exp = self.hero.exp

        self.level, self.current_exp, self.next_level_exp = \
                GLOBAL.LEVEL_TOTALEXP[self.exp]

        self.attack, self.defense, self.hp = \
                cal_hero_property(self.original_id, self.level)

        self.additional_attributes()

    def additional_attributes(self):
        pass


