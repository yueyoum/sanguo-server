# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-9-16'


from core.affairs import Affairs

from utils.decorate import message_response, function_check, operate_guard
from libs import pack_msg

from protomsg import HangGetRewardResponse, HangStartResponse

@message_response("HangSyncResponse")
@operate_guard('hang_sync', 3, keep_result=False)
def hang_sync(request):
    affairs = Affairs(request._char_id)
    affairs.send_hang_notify()
    return None


@message_response("HangGetRewardResponse")
def hang_get_reward(request):
    affairs = Affairs(request._char_id)
    drop = affairs.get_hang_reward()

    msg = HangGetRewardResponse()
    msg.ret = 0
    msg.drop.MergeFrom(drop)

    return pack_msg(msg)

@message_response("HangStartResponse")
@function_check(7)
def hang_start(request):
    req = request._proto

    affairs = Affairs(request._char_id)
    drop = affairs.start_hang(req.city_id)

    msg = HangStartResponse()
    msg.ret = 0
    if drop:
        msg.drop.MergeFrom(drop)

    return pack_msg(msg)




