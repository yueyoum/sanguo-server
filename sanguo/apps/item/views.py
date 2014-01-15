# -*- coding: utf-8 -*-

import logging

from utils.decorate import message_response

from core.item import Item

logger = logging.getLogger('sanguo')

@message_response("StrengthEquipResponse")
def strengthen_equip(request):
    req = request._proto

    item = Item(request._char_id)
    item.equip_level_up(req.id)

    return None


@message_response("StepUpEquipResponse")
def step_up_equip(request):
    req = request._proto

    item = Item(request._char_id)
    item.equip_step_up(req.id, req.to_id)
    return None



@message_response("SellEquipResponse")
def sell_equip(request):
    req = request._proto

    item = Item(request._char_id)
    item.equip_sell(req.id)

    return None

@message_response("EmbedGemResponse")
def embed(request):
    req = request._proto
    item = Item(request._char_id)
    item.equip_embed(req.equip_id, req.hole_id, req.gem_id)
    return None


@message_response("UnEmbedGemResponse")
def unembed(request):
    req = request._proto
    item = Item(request._char_id)
    item.equip_embed(req.equip_id, req.hole_id, 0)

    return None
