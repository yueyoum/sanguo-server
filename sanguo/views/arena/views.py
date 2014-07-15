# -*- coding: utf-8 -*-

from core.arena import Arena
from utils.decorate import message_response, operate_guard, function_check
from preset.settings import OPERATE_INTERVAL_ARENA_PANEL

from libs import pack_msg
from protomsg import ArenaPanelResponse, ArenaResponse

__author__ = 'Wang Chao'
__date__ = '1/22/14'


@message_response("ArenaPanelResponse")
@operate_guard('arena_panel', OPERATE_INTERVAL_ARENA_PANEL, keep_result=True)
@function_check(8)
def arena_panel(request):
    arena = Arena(request._char_id)
    response = ArenaPanelResponse()
    response.ret = 0

    arena.fill_up_panel_msg(response.panel)
    return pack_msg(response)


@message_response("ArenaResponse")
@function_check(8)
def arena_battle(request):
    char_id = request._char_id

    arena = Arena(char_id)
    msg = arena.battle()

    response = ArenaResponse()
    response.ret = 0
    response.battle.MergeFrom(msg)

    return pack_msg(response)
