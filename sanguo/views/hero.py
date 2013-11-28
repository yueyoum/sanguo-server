import random
from django.http import HttpResponse

from core.exception import SanguoViewException
from core import notify
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
    print req
    _, _, char_id = request._decrypted_session.split(':')
    char_id = int(char_id)

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
    
    
    heros = save_hero(char_id, heros)
    char_heros = []
    for i in heros:
        #hid, oid, level = get_hero(i)
        #char_heros.append( Hero(hid, oid, level, []) )
        char_heros.append( get_cache_hero(i) )
    
    notify.add_hero_notify(request._decrypted_session, char_heros)


    response = GetHeroResponse()
    response.ret = 0
    response.mode = req.mode
    # FIXME
    response.free_times = 10

    data = pack_msg(response)
    return HttpResponse(data, content_type="text/plain")


def merge_hero(request):
    req = request._proto
    print req
    _, _, char_id = request._decrypted_session.split(':')
    char_id = int(char_id)

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

    print "choosing_id =", choosing_id

    for _id in using_hero_ids:
        delete_hero(_id)

    new_hero_id = save_hero(char_id, choosing_id)[0]
    

    notify.remove_hero_notify(request._decrypted_session, using_hero_ids)
    notify.add_hero_notify(
        request._decrypted_session,
        #[Hero(new_hero_id, choosing_id, 1, [])]
        [ get_cache_hero(new_hero_id) ]
    )

    response = MergeHeroResponse()
    response.ret = 0

    data = pack_msg(response)
    return HttpResponse(data, content_type="text/plain")


