# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-10-15'

from utils.decorate import message_response

from core.vip import VIP
from utils import pack_msg
from protomsg import VIPGetRewardResponse

@message_response("VIPGetRewardResponse")
def vip_get_reward(request):
    req = request._proto
    char_id = request._char_id

    vip = VIP(char_id)
    reward_msg = vip.get_reward(req.vip)

    response = VIPGetRewardResponse()
    response.ret = 0
    response.reward.MergeFrom(reward_msg)
    return pack_msg(response)
