# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/21/14'

from utils import pack_msg
from utils.decorate import message_response
from core.plunder import Plunder
import protomsg



@message_response("PlunderListResponse")
def plunder_list(request):
    char_id = request._char_id
    p = Plunder(char_id)
    res = p.get_plunder_list()

    response = protomsg.PlunderListResponse()
    response.ret = 0

    for _id, name, gold, power, is_robot in res:
        plunder = response.plunders.add()
        plunder.id = _id
        plunder.name = name
        plunder.gold = gold
        plunder.power = power

    return pack_msg(response)


@message_response("PlunderResponse")
def plunder(request):
    req = request._proto
    char_id = request._char_id

    p = Plunder(char_id)
    msg, drop_gold, drop_official_exp, drop_hero_id = p.plunder(req.id)

    response = protomsg.PlunderResponse()
    response.ret = 0
    response.battle.MergeFrom(msg)
    response.drop.gold = drop_gold
    response.drop.official_exp = drop_official_exp
    if drop_hero_id:
        response.drop.heros.append(drop_hero_id)

    return pack_msg(response)

