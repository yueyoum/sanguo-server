import random
import base64

from django.http import HttpResponse

from models import Character, CharHero

from core.exception import SanguoViewException
from core import notify
from core import GLOBAL
from core import services

import protomsg
from protomsg import (
        CreateCharacterResponse,
        GetHeroResponse,
        MergeHeroResponse,
        SetFormationResponse,
        )

from utils import pack_msg
from utils import crypto


def create_character(request):
    req = request._proto
    print req

    if len(req.name) > 7:
        raise SanguoViewException(202, "CreateCharacterResponse")

    account_id, server_id = request._decrypted_session.split(':')
    account_id, server_id = int(account_id), int(server_id)

    if Character.objects.filter(account_id=account_id, server_id=server_id).exists():
        raise SanguoViewException(200, "CreateCharacterResponse")

    if Character.objects.filter( server_id=server_id,name=req.name).exists():
        raise SanguoViewException(201, "CreateCharacterResponse")


    char = Character.objects.create(
            account_id = account_id,
            server_id = server_id,
            name = req.name
            )

    init_heros = services.get_random_heros(3)
    char_heros_list = [
            CharHero(char=char, hero_id=hero["id"]) for hero in init_heros
            ]
    char_heros = CharHero.multi_create(char_heros_list)

    new_session = '%s:%d' % (request._decrypted_session, char.id)
    new_session = crypto.encrypt(new_session)

    response = CreateCharacterResponse()
    response.ret = 0
    data = pack_msg(response, new_session)

    notify.login_notify(request._decrypted_session, char, hero_objs=char_heros)
    return HttpResponse(data, content_type="text/plain")


def get_hero(request):
    req = request._proto
    print req
    _, _, char_id = request._decrypted_session.split(':')
    char_id = int(char_id)

    info = GLOBAL.GET_HERO[req.mode]
    # TODO check cost

    prob = random.randint(1, 100)
    get_probs = info['prob'].items()
    get_probs.sort(key=lambda item: item[1])

    for target_quality, target_prob in get_probs:
        if target_prob >= prob:
            break

    print "prob =", prob, "target_quality =", target_quality

    hero_list = services.get_hero_by_quality(target_quality)

    if req.ten:
        heros = [random.choice(hero_list) for i in range(10)]
    else:
        heros = [random.choice(hero_list)]
    
    char_heros_list = [
            CharHero(char_id=char_id, hero_id=hero["id"]) for hero in heros
            ]

    char_heros = CharHero.multi_create(char_heros_list)
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

    original_ids = CharHero.objects.filter(char_id=char_id, id__in=using_hero_ids).values_list('hero_id', flat=True)
    print "original_ids =", original_ids
    if len(original_ids) != len(using_hero_ids):
        hero_objs = CharHero.objects.filter(char__id=char_id)
        notify.hero_notify(request._decrypted_session, hero_objs)
        raise SanguoViewException(300, "MergeHeroResponse")

    original_quality = [GLOBAL.HEROS[hid]['quality_id'] for hid in original_ids]

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


    all_hero_ids = GLOBAL.HEROS.keys()
    if original_quality[0] == 1:
        while True:
            choosing_id = random.choice(all_hero_ids)
            if choosing_id not in original_ids:
                break
    else:
        choosing_id = random.choice(all_hero_ids)

    print "choosing_id =", choosing_id

    CharHero.objects.filter(char_id=char_id, id__in=using_hero_ids).delete()

    new_char_hero = CharHero.objects.create(
            char_id = char_id,
            hero_id = choosing_id
            )

    notify.remove_hero_notify(request._decrypted_session, using_hero_ids)
    notify.add_hero_notify(request._decrypted_session, [new_char_hero])

    response = MergeHeroResponse()
    response.ret = 0

    data = pack_msg(response)
    return HttpResponse(data, content_type="text/plain")


def set_formation(request):
    req = request._proto
    print req
    _, _, char_id = request._decrypted_session.split(':')
    char_id = int(char_id)

    positions = req.positions
    # TODO check positions

    formation_msg = getattr(protomsg, "Formation")()
    formation_msg.positions.MergeFrom(positions)
    encoded_position = base64.b64encode(formation_msg.SerializeToString())
    Character.objects.filter(id=char_id).update(formation=encoded_position)
    notify.formation_notify(request._decrypted_session, formation=encoded_position)

    response = SetFormationResponse()
    response.ret = 0

    data = pack_msg(response)
    return HttpResponse(data, content_type="text/plain")

