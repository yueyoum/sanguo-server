# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-11-20'


from utils.decorate import message_response
from core.horse import Horse
from utils import pack_msg
from protomsg import HorseStrengthResponse

@message_response("HorseStrengthResponse")
def strength(request):
    req = request._proto
    char_id = request._char_id

    h = Horse(char_id)
    new_horse = h.strength(req.id, req.method)

    response = HorseStrengthResponse()
    response.ret = 0
    response.new_horse.MergeFrom(new_horse.make_msg())
    return pack_msg(response)

@message_response("HorseStrengthConfirmResponse")
def strength_confirm(request):
    req = request._proto
    char_id = request._char_id
    h = Horse(char_id)

    cancel = True if req.tp == 2 else False
    h.strength_confirm(cancel)
    return None

@message_response("HorseEvolutionResponse")
def evolution(request):
    req = request._proto
    char_id = request._char_id

    h = Horse(char_id)
    h.evolution(req.horse_id, req.horse_soul_id)
    return None
