# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-11-6'

from utils.decorate import message_response

from core.activity import ActivityStatic
from utils import pack_msg
from protomsg import ActivityGetRewardResponse

@message_response("ActivityGetRewardResponse")
def get_reward(request):
    req = request._proto

    ac = ActivityStatic(request._char_id)
    reward = ac.get_reward(req.condition_id)

    response = ActivityGetRewardResponse()
    response.ret = 0
    response.reward.MergeFrom(reward)
    return pack_msg(response)
