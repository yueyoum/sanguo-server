# -*- coding: utf-8 -*-
import protomsg
from libs import pack_msg
from utils.decorate import message_response, operate_guard, function_check

from core.arena import Arena

__author__ = 'Wang Chao'
__date__ = '1/22/14'


@message_response("ArenaPanelResponse")
@operate_guard('arena_panel', 10, keep_result=True)
@function_check(8)
def arena_panel(request):
    arena = Arena(request._char_id)
    response = protomsg.ArenaPanelResponse()
    response.ret = 0

    arena._fill_up_panel_msg(response.panel)
    return pack_msg(response)

@message_response("ArenaResponse")
@operate_guard('arena_battle', 15, keep_result=False)
@function_check(8)
def arena_battle(request):
    char_id = request._char_id

    arena = Arena(char_id)
    msg = arena.battle()

    response = protomsg.ArenaResponse()
    response.ret = 0
    response.battle.MergeFrom(msg)

    return pack_msg(response)
