# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/21/14'

from libs import pack_msg
from utils.decorate import message_response, operate_guard
from core.plunder import Plunder
import protomsg



@message_response("PlunderListResponse")
@operate_guard('plunder_list', 10, keep_result=True)
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
    got_hero_id, got_equipments, got_gems, got_stuffs, got_gold = p.get_reward(req.tp)

    response = protomsg.PlunderGetRewardResponse()
    response.ret = 0
    response.tp = req.tp

    if got_hero_id:
        response.reward.heros.append(got_hero_id)
    if got_equipments:
        for _id, level, step in got_equipments:
            e = response.reward.equipments.add()
            e.id = _id
            e.level = level
            e.step = step
            e.amount = 1
    if got_gems:
        for _id, amount in got_gems:
            g = response.reward.gems.add()
            g.id = _id
            g.amount = amount
    if got_stuffs:
        for _id, amount in got_stuffs:
            s = response.reward.stuffs.add()
            s.id = _id
            s.amount = amount
    if got_gold:
        response.reward.gold = got_gold

    return pack_msg(response)

