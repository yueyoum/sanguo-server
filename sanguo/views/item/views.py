# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/9/14'


from utils.decorate import message_response
from core.item import Item
from libs import pack_msg

from protomsg import StrengthEquipResponse


@message_response("StrengthEquipResponse")
def strengthen_equip(request):
    req = request._proto

    item = Item(request._char_id)
    equip_msgs = item.equip_level_up(req.id, req.quick)

    response = StrengthEquipResponse()
    response.ret = 0
    for m in equip_msgs:
        equip_msg = response.equips.add()
        equip_msg.MergeFrom(m)
    return pack_msg(response)


@message_response("StepUpEquipResponse")
def step_up_equip(request):
    req = request._proto

    item = Item(request._char_id)
    item.equip_step_up(req.id)
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


@message_response("MergeGemResponse")
def merge(request):
    req = request._proto
    item = Item(request._char_id)
    item.gem_merge(req.id)
    return None

@message_response("SpecialEquipmentBuyResponse")
def special_buy(request):
    req = request._proto
    item = Item(request._char_id)
    item.special_buy(req.socket_id, req.tp)
    return None
