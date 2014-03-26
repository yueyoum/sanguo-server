# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '12/31/13'

from core.friend import Friend
from core.character import Char, get_char_ids_by_level_range
from utils import pack_msg
from utils.decorate import message_response, operate_guard

import protomsg
from protomsg import FRIEND_NOT

LEVEL_DIFF = 10

@message_response("PlayerListResponse")
@operate_guard('friend_player_list', 10, keep_result=True)
def player_list(request):
    char_id = request._char_id
    server_id = request._server_id
    char = Char(char_id)
    level = char.cacheobj.level

    char_ids = get_char_ids_by_level_range(server_id, level-LEVEL_DIFF, level+LEVEL_DIFF)

    f = Friend(char_id)
    res = []
    for c in char_ids:
        if c == char_id:
            continue
        if f.is_general_friend(c):
            continue

        res.append(c)
        if len(res) >= 5:
            break

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
@operate_guard('friend_refresh', 10, keep_result=True)
def refresh(request):
    f = Friend(request._char_id)
    f.send_friends_notify()
    return None
