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

