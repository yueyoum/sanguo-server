import random

from django.http import HttpResponse

from models import Character, CharHero

from core.exception import SanguoViewException
from core import notify
from core import GLOBAL
from core.drives import document_char

from core.formation import (
        decode_formation,
        encode_formation,
        encode_formation_with_raw_data,
        )

from core.character import get_char_formation
from core.battle.tests import _PVE

import protomsg
from protomsg import (
        CreateCharacterResponse,
        GetHeroResponse,
        MergeHeroResponse,
        SetFormationResponse,
        )

from utils import pack_msg
from utils import crypto


def setUp():
    monster = GLOBAL.MONSTERS.values()[0]
    new_monsters = {}
    for i in range(9):
        # monster['skills'] = _random_skill_ids(random.randint(1, 3))
        monster['skills'] = [2]
        new_monsters[i] = monster

    GLOBAL.MONSTERS = new_monsters

setUp()


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

    init_hero_ids = GLOBAL.HEROS.get_random_hero_ids(3)
    char_heros_list = [
            CharHero(char=char, hero_id=hid) for hid in init_hero_ids
            ]
    char_heros = CharHero.multi_create(char_heros_list)

    encoded_formation = encode_formation_with_raw_data(
            9,
            [
                char_heros[0].id, 0, 0,
                char_heros[1].id, 0, 0,
                char_heros[2].id, 0, 0,
            ]
            )

    document_char.set(char.id, formation=encoded_formation)

    new_session = '%s:%d' % (request._decrypted_session, char.id)
    new_session = crypto.encrypt(new_session)

    response = CreateCharacterResponse()
    response.ret = 0
    data = pack_msg(response, new_session)

    notify.login_notify(
            request._decrypted_session,
            char,
            hero_objs=char_heros,
            formation=encoded_formation,
            )

    return HttpResponse(data, content_type="text/plain")


def get_hero(request):
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
    
    char_heros_list = [
            CharHero(char_id=char_id, hero_id=hid) for hid in heros
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

    hero_ids = req.hero_ids

    if len(hero_ids) != 9:
        raise SanguoViewException(400, "SetFormationResponse")

    for i in range(0, 9, 3):
        if hero_ids[i] == hero_ids[i+1] == hero_ids[i+2] == 0:
            raise SanguoViewException(400, "SetFormationResponse")

    old_formation = get_char_formation(char_id)

    formation_msg = decode_formation(old_formation)

    formation_msg.ClearField('hero_ids')
    formation_msg.hero_ids.MergeFrom(hero_ids)
    encoded_formation = encode_formation(formation_msg)

    document_char.set(char_id, formation=encoded_formation)

    notify.formation_notify(request._decrypted_session, formation=encoded_formation)

    response = SetFormationResponse()
    response.ret = 0

    data = pack_msg(response)
    return HttpResponse(data, content_type="text/plain")



def pve(request):
    msg = protomsg.Battle()
    b = _PVE(0, 0, msg)
    b.start()

    response = protomsg.PVEResponse()
    response.ret = 0
    response.stage_id = 1
    response.battle.MergeFrom(msg)

    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')

