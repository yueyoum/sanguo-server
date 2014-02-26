# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/26/14'

from utils.decorate import message_response
from core.stage import TeamBattle

@message_response("TeamBattleEnterResponse")
def enter(request):
    req = request._proto
    tb = TeamBattle(request._char_id)
    tb.enter(req.id)
    return None

@message_response("TeamBattleStartResponse")
def start(request):
    req = request._proto
    tb = TeamBattle(request._char_id)
    friend_ids = [int(i) for i in req.friend_ids]
    tb.start(friend_ids)
    return None

@message_response("TeamBattleIncrTimeResponse")
def incr_time(request):
    tb = TeamBattle(request._char_id)
    tb.incr_time()
    return None

@message_response("TeamBattleGetRewardResponse")
def get_reward(request):
    tb = TeamBattle(request._char_id)
    tb.get_reward()
    return None

