# -*- coding: utf-8 -*-
import protomsg
from utils import pack_msg
from utils.decorate import message_response

from core.arena import Arena

__author__ = 'Wang Chao'
__date__ = '1/22/14'


@message_response("ArenaResponse")
def arena_battle(request):
    req = request._proto
    char_id = request._char_id

    arena = Arena(char_id)
    msg = arena.battle()

    # FIXME
    score = 0
    if msg.self_win:
        score = 100

    response = protomsg.ArenaResponse()
    response.ret = 0
    response.battle.MergeFrom(msg)
    response.score = score

    return pack_msg(response)
