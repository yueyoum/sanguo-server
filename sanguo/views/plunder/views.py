# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/21/14'

from libs import pack_msg
from utils.decorate import message_response, operate_guard, function_check
from core.character import Char
from core.plunder import Plunder
from core.attachment import standard_drop_to_attachment_protomsg
from preset.settings import OPERATE_INTERVAL_PLUNDER_BATTLE, OPERATE_INTERVAL_PLUNDER_REFRESH
from protomsg import PlunderResponse, PlunderRefreshResponse

from preset import errormsg


@message_response("PlunderRefreshResponse")
@operate_guard('plunder_refresh', OPERATE_INTERVAL_PLUNDER_REFRESH, keep_result=False)
@function_check(9)
def plunder_refresh(request):
    req = request._proto
    char_id = request._char_id
    p = Plunder(char_id)
    target = p.get_plunder_target(req.city_id)

    response = PlunderRefreshResponse()
    if not target:
        response.ret = errormsg.PLUNDER_NO_RIVAL
    else:
        response.ret = 0
        response.plunder.MergeFrom(target.make_plunder_msg(Char(char_id).mc.level))

    return pack_msg(response)


@message_response("PlunderResponse")
@operate_guard('plunder', OPERATE_INTERVAL_PLUNDER_BATTLE, keep_result=False)
@function_check(9)
def plunder(request):
    char_id = request._char_id

    p = Plunder(char_id)
    msg, drop = p.plunder()

    response = PlunderResponse()
    response.ret = 0
    response.battle.MergeFrom(msg)
    response.drop.MergeFrom(standard_drop_to_attachment_protomsg(drop))

    return pack_msg(response)
