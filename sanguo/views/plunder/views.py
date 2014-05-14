# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/21/14'

from libs import pack_msg
from utils.decorate import message_response, operate_guard, function_check
from core.plunder import Plunder
import protomsg



@message_response("PlunderListResponse")
@operate_guard('plunder_list', 10, keep_result=True)
@function_check(9)
def plunder_list(request):
    char_id = request._char_id
    p = Plunder(char_id)
    res = p.get_plunder_list()

    response = protomsg.PlunderListResponse()
    response.ret = 0

    for _id, name, power, formation, is_robot, gold in res:
        plunder = response.plunders.add()
        plunder.id = _id
        plunder.name = name
        plunder.gold = gold
        plunder.power = power
        plunder.hero_original_ids.extend(formation)

    return pack_msg(response)


@message_response("PlunderResponse")
@operate_guard('plunder', 15, keep_result=False)
@function_check(9)
def plunder(request):
    req = request._proto
    char_id = request._char_id

    p = Plunder(char_id)
    msg = p.plunder(req.id)

    response = protomsg.PlunderResponse()
    response.ret = 0
    response.battle.MergeFrom(msg)

    return pack_msg(response)

@message_response("PlunderGetRewardResponse")
def get_reward(request):
    req = request._proto
    char_id = request._char_id

    p = Plunder(char_id)
    attachment_msg = p.get_reward(req.tp)

    response = protomsg.PlunderGetRewardResponse()
    response.ret = 0
    response.tp = req.tp
    response.reward.MergeFrom(attachment_msg)

    return pack_msg(response)

