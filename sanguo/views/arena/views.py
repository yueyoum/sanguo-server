# -*- coding: utf-8 -*-
import protomsg
from utils import pack_msg
from utils.decorate import message_response

from core.arena import Arena

__author__ = 'Wang Chao'
__date__ = '1/22/14'


@message_response("ArenaPanelResponse")
def arena_panel(request):
    arena = Arena(request._char_id)
    response = protomsg.ArenaPanelResponse()
    response.ret = 0

    arena._fill_up_panel_msg(response.panel)
    return pack_msg(response)

@message_response("ArenaResponse")
def arena_battle(request):
    char_id = request._char_id

    arena = Arena(char_id)
    msg = arena.battle()

    response = protomsg.ArenaResponse()
    response.ret = 0
    response.battle.MergeFrom(msg)

    return pack_msg(response)
