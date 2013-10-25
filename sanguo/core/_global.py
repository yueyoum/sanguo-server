# -*- coding: utf-8 -*-


from utils.decorate import LazyDict

@LazyDict()
def _all_heros():
    from apps.hero.models import Hero
    heros = Hero.objects.all().values()
    data = {item['id']: item for item in heros}
    return data


# 抽卡
GET_HERO = {
    1: {
        'cost_gem': 300,
        'cost_gold': 0,
        'prob': {1: 8, 2: 92}
        },
    2: {
        'cost_gem': 300,
        'cost_gold': 0,
        'prob': {1: 4, 2: 20, 3: 76}
        },
    3: {
        'cost_gem': 300,
        'cost_gold': 0,
        'prob': {2: 5, 3: 20, 4: 75}
        },
}





class _Global(object):
    pass


GLOBAL = _Global()
GLOBAL.HERO = _all_heros()
GLOBAL.GET_HERO = GET_HERO

