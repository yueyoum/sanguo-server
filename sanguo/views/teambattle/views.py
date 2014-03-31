# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/26/14'

from utils.decorate import message_response
from core.stage import TeamBattle


@message_response("TeamBattleStartResponse")
def start(request):
    req = request._proto
    tb = TeamBattle(request._char_id)
    friend_ids = [int(i) for i in req.friend_ids]
    tb.start(req.id, friend_ids)
    return None

