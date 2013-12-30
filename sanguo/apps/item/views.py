# -*- coding: utf-8 -*-

import logging
from django.http import HttpResponse

from apps.item.cache import get_cache_equipment
from apps.item.models import Equipment
from core.equip import delete_equip, embed_gem
from core.character import Char
from core.gem import save_gem
from core.exception import InvalidOperate, GoldNotEnough
from protomsg import (EmbedGemResponse, SellEquipResponse,
                      StrengthEquipResponse, UnEmbedGemResponse)
from utils import pack_msg


logger = logging.getLogger('sanguo')


def strengthen_equip(request):
    req = request._proto
    char_id = request._char_id

    char = Char(char_id)
    char_equip_ids = char.equip_ids

    if req.id not in char_equip_ids:
        logger.warning("Strengthen Equip. req.id: {0} NOT in Char: {1}. {2}".format(
            req.id, char_id, char_equip_ids
        ))
        raise InvalidOperate("StrengthEquipResponse")

    for _id in req.cost_ids:
        if _id not in char_equip_ids:
            logger.warning("Strengthen Equip. req.cost_id: {0} NOT in Char: {1}. {2}".format(
                _id, char_id, char_equip_ids
            ))
            raise InvalidOperate("StrengthEquipResponse")

    target_equip = Equipment.objects.get(id=req.id)
    gold_needs = target_equip.level * 100

    cache_char = char.cacheobj
    if gold_needs > cache_char.gold:
        logger.debug("Strengthen Equip. Char {0} NOT enough gold. {1}, needs {2}".format(
            char_id, cache_char.gold, gold_needs
        ))
        raise GoldNotEnough("StrengthEquipResponse")

    char.update(gold=-gold_needs)

    all_exp = 0
    for _id in req.cost_ids:
        cache_equip = get_cache_equipment(_id)
        gems = [(gid, 1) for gid in cache_equip.gems]
        if gems:
            save_gem(gems, char_id)
        all_exp += cache_equip.whole_exp()

    update_process = target_equip.update_process(target_equip.exp, all_exp)

    new_level, new_exp = update_process.end
    logger.debug("Strengthen Equip: Char {0}, Equip {1}, original level {2}, exp {3} => new level {4} exp {5}".format(
        char_id, req.id, target_equip.level, target_equip.exp, new_level, new_exp
    ))

    target_equip.exp = new_exp
    target_equip.level = new_level
    target_equip.save()

    delete_equip([_id for _id in req.cost_ids])

    response = StrengthEquipResponse()
    response.ret = 0
    response.id = req.id
    for p in update_process:
        _p = response.processes.add()
        _p.level, _p.cur_exp, _p.max_exp = p

    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')


def sell_equip(request):
    req = request._proto
    char_id = request._char_id

    char = Char(char_id)
    char_equip_ids = char.equip_ids

    for _id in req.ids:
        if _id not in char_equip_ids:
            logger.warning("Sell Equip: Equip {0} NOT in Char {1}, {2}".format(
                _id, char_id, char_equip_ids
            ))
            raise InvalidOperate("SellEquipResponse")

    all_gold = 0
    for _id in req.ids:
        cache_equip = get_cache_equipment(_id)
        all_gold += cache_equip.sell_value()

    logger.debug("Sell Equip: Char {0} sell {1}, get gold {2}".format(
        char_id, req.ids, all_gold
    ))

    delete_equip([_id for _id in req.ids])
    char.update(gold=all_gold)

    response = SellEquipResponse()
    response.ret = 0
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')


def embed(request):
    req = request._proto
    char_id = request._char_id

    embed_gem(char_id, req.equip_id, req.hole_id, req.gem_id)

    response = EmbedGemResponse()
    response.ret = 0
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')


def unembed(request):
    req = request._proto
    char_id = request._char_id

    embed_gem(char_id, req.equip_id, req.hole_id, 0)

    response = UnEmbedGemResponse()
    response.ret = 0
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')
