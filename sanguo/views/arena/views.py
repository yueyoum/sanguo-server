# -*- coding: utf-8 -*-

from core.arena import Arena
from core.attachment import standard_drop_to_attachment_protomsg
from utils.decorate import message_response, operate_guard, function_check
from preset.settings import OPERATE_INTERVAL_ARENA_PANEL

from libs import pack_msg
from protomsg import ArenaResponse


__author__ = 'Wang Chao'
__date__ = '1/22/14'


@message_response("ArenaPanelResponse")
@operate_guard('arena_panel', OPERATE_INTERVAL_ARENA_PANEL, keep_result=True)
@function_check(8)
def arena_panel(request):
    response = Arena(request._char_id).make_panel_response()
    return pack_msg(response)


@message_response("ArenaResponse")
@function_check(8)
def arena_battle(request):
    char_id = request._char_id

    arena = Arena(char_id)
    msg, drop = arena.battle()

    response = ArenaResponse()
    response.ret = 0
    response.battle.MergeFrom(msg)
    response.drop.MergeFrom(standard_drop_to_attachment_protomsg(drop))
    return pack_msg(response)
