# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '12/31/13'

from core.friend import Friend
from libs import pack_msg
from utils.decorate import message_response, operate_guard
from preset.settings import OPERATE_INTERVAL_FRIEND_CANDIDATE_LIST, OPERATE_INTERVAL_FRIEND_REFRESH

import protomsg
from protomsg import FRIEND_NOT


@message_response("PlayerListResponse")
@operate_guard('friend_candidate_list', OPERATE_INTERVAL_FRIEND_CANDIDATE_LIST, keep_result=True)
def candidate_list(request):
    char_id = request._char_id

    f = Friend(char_id)
    res = f.candidate_list()

    response = protomsg.PlayerListResponse()
    response.ret = 0
    for r in res:
        msg = response.players.add()
        f._msg_friend(msg, r, FRIEND_NOT)

    return pack_msg(response)


@message_response("FriendAddResponse")
def add(request):
    req = request._proto
    f = Friend(request._char_id)
    f.add(req.id, req.name)
    return None


@message_response("FriendTerminateResponse")
def terminate(request):
    req = request._proto
    f = Friend(request._char_id)
    f.terminate(req.id)
    return None


@message_response("FriendCancelResponse")
def cancel(request):
    req = request._proto
    f = Friend(request._char_id)
    f.cancel(req.id)
    return None


@message_response("FriendAcceptResponse")
def accept(request):
    req = request._proto
    f = Friend(request._char_id)
    f.accept(req.id)
    return None


@message_response("FriendRefuseResponse")
def refuse(request):
    req = request._proto
    f = Friend(request._char_id)
    f.refuse(req.id)
    return None


@message_response("FriendRefreshResponse")
@operate_guard('friend_refresh', OPERATE_INTERVAL_FRIEND_REFRESH, keep_result=True)
def refresh(request):
    f = Friend(request._char_id)
    f.send_friends_notify()
    return None
