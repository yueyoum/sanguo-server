# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/9/14'

from core.stage import Stage, EliteStage, ActivityStage
from core.attachment import standard_drop_to_attachment_protomsg
from libs import pack_msg
from utils.decorate import message_response, operate_guard, function_check
from preset.settings import OPERATE_INTERVAL_PVE, OPERATE_INTERVAL_PVE_ELITE

import protomsg


@message_response("ActivityStagePVEResponse")
def activity_pve(request):
    req = request._proto
    stage = ActivityStage(request._char_id)

    battle_msg = stage.battle(req.stage_id)

    if battle_msg.self_win:
        drop = stage.save_drop()
    else:
        drop = {}

    response = protomsg.ActivityStagePVEResponse()
    response.ret = 0
    response.stage_id = req.stage_id
    response.battle.MergeFrom(battle_msg)
    if drop:
        response.drop.MergeFrom(standard_drop_to_attachment_protomsg(drop))

    return pack_msg(response)



@message_response("ElitePVEResponse")
@operate_guard('elite_pve', OPERATE_INTERVAL_PVE_ELITE, keep_result=False)
@function_check(11)
def elite_pve(request):
    req = request._proto
    stage = EliteStage(request._char_id)

    battle_msg = stage.battle(req.stage_id)
    if battle_msg.self_win:
        drop = stage.save_drop()
    else:
        drop = {}

    response = protomsg.ElitePVEResponse()
    response.ret = 0
    response.stage_id = req.stage_id
    response.battle.MergeFrom(battle_msg)
    if drop:
        response.drop.MergeFrom(standard_drop_to_attachment_protomsg(drop))

    return pack_msg(response)


@message_response("EliteStageResetResponse")
def elite_reset(request):
    req = request._proto
    stage = EliteStage(request._char_id)
    stage.reset_one(req.id)
    return None

@message_response("EliteStageResetTotalResponse")
def elite_reset_total(request):
    stage = EliteStage(request._char_id)
    stage.reset_total()
    return None


@message_response("PVEResponse")
@operate_guard('pve', OPERATE_INTERVAL_PVE, keep_result=False)
def pve(request):
    req = request._proto
    stage = Stage(request._char_id)
    battle_msg = stage.battle(req.stage_id)

    if battle_msg.self_win:
        drop = stage.save_drop(req.stage_id, first=stage.first, star=stage.first_star)
    else:
        drop = {}

    response = protomsg.PVEResponse()
    response.ret = 0
    response.stage_id = req.stage_id
    response.battle.MergeFrom(battle_msg)
    if drop:
        response.drop.MergeFrom(standard_drop_to_attachment_protomsg(drop))

    return pack_msg(response)

