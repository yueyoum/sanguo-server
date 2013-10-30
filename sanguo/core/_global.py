# -*- coding: utf-8 -*-

from utils.decorate import LazyDict
from preset import *

LINE_SEP = "\r\n"

@LazyDict()
def _all_heros():
    from apps.constant.models import Hero
    heros = Hero.objects.values()
    data = {item['id']: item for item in heros}
    return data

@LazyDict()
def _get_heros():
    from apps.constant.models import GetHero
    info = GetHero.objects.values()

    def _parse_prob(text):
        text = text.strip(LINE_SEP)
        lines = text.split(LINE_SEP)

        probs = []
        for line in lines:
            line = line.strip(',')
            qid, prob = line.split(',')
            probs.append((int(qid), int(prob)))

        probs.sort(key=lambda item: item[1])
        return probs


    data = {}
    for i in info:
        get_id = i['mode']
        data[get_id] = {
                'gem': i['gem'],
                'prob': _parse_prob(i['quality_and_prob'])
                }
    return data



# HEROS = _all_heros()
GET_HERO = _get_heros()


