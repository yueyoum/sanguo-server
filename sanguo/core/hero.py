from core import GLOBAL


def cal_hero_property(original_id, level):
    attack = 20 + level * (7 + GLOBAL.HEROS[original_id]['attack_grow'])
    defense = 15 + level * (6 + GLOBAL.HEROS[original_id]['defense_grow'])
    hp = 45 + level * (15 + GLOBAL.HEROS[original_id]['hp_grow'])

    return attack, defense, hp



class Hero(object):
    def __init__(self, hid, original_id, exp, skills):
        self.id = hid
        self.original_id = original_id 
        self.exp = exp
        self.skills = skills

        self.level, self.current_exp, self.next_level_exp = \
                GLOBAL.LEVEL_TOTALEXP[self.exp]

        self.attack, self.defense, self.hp = \
                cal_hero_property(self.original_id, self.level)

        self.crit = 20
        self.dodge = 20

        self.additional_attributes()

    def additional_attributes(self):
        pass


