# -*- coding: utf-8 -*-
import random

from django.http import HttpResponse

from core import GLOBAL
from core.character import Char
from core.exception import BadMessage, SanguoViewException, SyceeNotEnough
from protomsg import GetHeroResponse, MergeHeroResponse
from utils import pack_msg

DRAW_HERO = GLOBAL.SETTINGS.DRAW_HERO


def pick_hero(request):
    req = request._proto
    char_id = request._char_id
    
    char = Char(char_id)
    cache_char = char.cacheobj

    try:
        info = DRAW_HERO[req.mode]
    except KeyError:
        raise BadMessage("GetHeroResponse")
    
    if req.ten:
        pick_times = 10
    else:
        pick_times = 1
    
    using_sycee = pick_times * info['sycee']
    if using_sycee > cache_char.sycee:
        raise SyceeNotEnough("GetHeroResponse")
    
    prob = random.randint(1, 100)

    for target_quality, target_prob in info['prob']:
        if target_prob >= prob:
            break

    print "prob =", prob, "target_quality =", target_quality

    hero_id_list = GLOBAL.HEROS.get_hero_ids_by_quality(target_quality)

    if req.ten:
        heros = [random.choice(hero_id_list) for i in range(10)]
    else:
        heros = [random.choice(hero_id_list)]
    
    char.update(sycee=-using_sycee)
    char.save_hero(heros)
    
    response = GetHeroResponse()
    response.ret = 0
    response.mode = req.mode
    # FIXME
    # CRON
    response.free_times = 10

    data = pack_msg(response)
    return HttpResponse(data, content_type="text/plain")


def merge_hero(request):
    req = request._proto
    char_id = request._char_id
    
    char = Char(char_id)
    in_bag_hero_ids = char.in_bag_hero_ids()

    using_hero_ids = req.using_hero_ids
    for i in using_hero_ids:
        if i not in in_bag_hero_ids:
            raise SanguoViewException(300, "MergeHeroResponse")

    heros = char.heros_dict
    original_ids = []
    for i in using_hero_ids:
        original_ids.append(heros[i])

    original_quality = [GLOBAL.HEROS[hid]['quality'] for hid in original_ids]

    if len(set(original_quality)) != 1:
        raise SanguoViewException(301, "MergeHeroResponse")

    if len(using_hero_ids) == 2:
        target_quality = 1
        if original_quality[0] != 1:
            raise SanguoViewException(302, "MergeHeroResponse")
    elif len(using_hero_ids) == 8:
        target_quality = original_quality[0] - 1
        if original_quality[0] == 1:
            raise SanguoViewException(302, "MergeHeroResponse")
    else:
        raise SanguoViewException(302, "MergeHeroResponse")


    all_hero_ids = GLOBAL.HEROS.get_hero_ids_by_quality(target_quality)
    if original_quality[0] == 1:
        while True:
            choosing_id = random.choice(all_hero_ids)
            if choosing_id not in original_ids:
                break
    else:
        choosing_id = random.choice(all_hero_ids)

    char.delete_hero(using_hero_ids)
    char.save_hero(choosing_id)

    response = MergeHeroResponse()
    response.ret = 0

    data = pack_msg(response)
    return HttpResponse(data, content_type="text/plain")
