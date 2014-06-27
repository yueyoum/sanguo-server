# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/21/14'

from libs import pack_msg
from utils.decorate import message_response, operate_guard, function_check
from core.plunder import Plunder
from preset.settings import OPERATE_INTERVAL_PLUNDER_BATTLE, OPERATE_INTERVAL_PLUNDER_LIST
from protomsg import PlunderListResponse, PlunderResponse, PlunderGetRewardResponse


@message_response("PlunderListResponse")
@operate_guard('plunder_list', OPERATE_INTERVAL_PLUNDER_LIST, keep_result=True)
@function_check(9)
def plunder_list(request):
    char_id = request._char_id
    p = Plunder(char_id)
    res = p.get_plunder_list()

    response = PlunderListResponse()
    response.ret = 0

    for _id, name, power, leader, formation, is_hang in res:
        plunder = response.plunders.add()
        plunder.id = _id
        plunder.name = name
        plunder.gold = 0
        plunder.power = power
        plunder.leader = leader
        plunder.hero_original_ids.extend(formation)
        # plunder.hang = is_hang

    return pack_msg(response)


@message_response("PlunderResponse")
@operate_guard('plunder', OPERATE_INTERVAL_PLUNDER_BATTLE, keep_result=False)
@function_check(9)
def plunder(request):
    req = request._proto
    char_id = request._char_id

    p = Plunder(char_id)
    msg = p.plunder(req.id)

    response = PlunderResponse()
    response.ret = 0
    response.battle.MergeFrom(msg)

    return pack_msg(response)

@message_response("PlunderGetRewardResponse")
def get_reward(request):
    req = request._proto
    char_id = request._char_id

    p = Plunder(char_id)
    attachment_msg = p.get_reward(req.tp)

    response = PlunderGetRewardResponse()
    response.ret = 0
    response.tp = req.tp
    response.reward.MergeFrom(attachment_msg)

    return pack_msg(response)
