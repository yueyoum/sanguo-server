import random
from django.http import HttpResponse

from core.exception import SanguoViewException
from core import GLOBAL
from core.hero import save_hero, delete_hero, Hero
from core.character import get_char_heros
from core.cache import get_cache_hero

from protomsg import (
    GetHeroResponse,
    MergeHeroResponse,
)

from utils import pack_msg



def pick_hero(request):
    req = request._proto
    char_id = request._char_id

    info = GLOBAL.GET_HERO[req.mode]
    # TODO check cost

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
    
    
    save_hero(char_id, heros)
    response = GetHeroResponse()
    response.ret = 0
    response.mode = req.mode
    # FIXME
    response.free_times = 10

    data = pack_msg(response)
    return HttpResponse(data, content_type="text/plain")


def merge_hero(request):
    req = request._proto
    char_id = request._char_id

    using_hero_ids = req.using_hero_ids

    heros = get_char_heros(char_id)
    original_ids = []
    for i in using_hero_ids:
        if i not in heros:
                raise SanguoViewException(300, "MergeHeroResponse")
        original_ids.append(heros[i])
                

    original_quality = [GLOBAL.HEROS[hid]['quality'] for hid in original_ids]

    if len(set(original_quality)) != 1:
        raise SanguoViewException(301, "MergeHeroResponse")

    if len(using_hero_ids) == 2:
        if original_quality[0] != 1:
            raise SanguoViewException(302, "MergeHeroResponse")
    elif len(using_hero_ids) == 8:
        if original_quality[0] == 1:
            raise SanguoViewException(302, "MergeHeroResponse")
    else:
        raise SanguoViewException(302, "MergeHeroResponse")


    all_hero_ids = GLOBAL.HEROS.all_ids()
    if original_quality[0] == 1:
        while True:
            choosing_id = random.choice(all_hero_ids)
            if choosing_id not in original_ids:
                break
    else:
        choosing_id = random.choice(all_hero_ids)

    delete_hero(char_id, using_hero_ids)
    save_hero(char_id, choosing_id)

    response = MergeHeroResponse()
    response.ret = 0

    data = pack_msg(response)
    return HttpResponse(data, content_type="text/plain")


