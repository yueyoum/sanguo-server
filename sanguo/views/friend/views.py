# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '12/31/13'

from core.friend import Friend
from core.character import Char
from apps.character.models import Character
from utils import pack_msg
from utils.decorate import message_response

import protomsg
from protomsg import FRIEND_NOT


@message_response("PlayerListResponse")
def player_list(request):
    char_id = request._char_id
    char = Char(char_id)
    level = char.cacheobj.level
    # FIXME

    f = Friend(char_id)
    chars = Character.objects.all()
    res = []
    for c in chars:
        if f.is_general_friend(c.id):
            continue

        res.append(c.id)
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

