import random

from core import GLOBAL

def get_random_heros(num):
    ids = GLOBAL.HEROS.keys()
    res = []
    while True:
        if len(res) >= num or not ids:
            break

        this_id = random.choice(ids)
        ids.remove(this_id)

        if this_id not in res:
            res.append(this_id)

    return [GLOBAL.HEROS[i] for i in res]
    
def get_hero_by_quality(quality):
    def _filter(h):
        return h["quality_id"] == quality
    return filter(_filter, GLOBAL.HEROS.values())


def cal_hero_property(hero_original_id, hero_level):
    attack = 20 + hero_level * (5 + GLOBAL.HEROS[hero_original_id]['attack_grow'])
    defense = 15 + hero_level * (4 + GLOBAL.HEROS[hero_original_id]['defense_grow'])
    hp = 45 + hero_level * (14 + GLOBAL.HEROS[hero_original_id]['hp_grow'])

    return attack, defense, hp

