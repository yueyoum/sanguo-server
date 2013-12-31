# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '12/31/13'


from django.http import HttpResponse
from core.friend import Friend
from core.character import Char
from apps.character.models import Character
from utils import pack_msg

import protomsg
from protomsg import FRIEND_NOT

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

    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')






def add(request):
    req = request._proto
    f = Friend(request._char_id)
    f.add(req.id, req.name)

    response = protomsg.FriendAddResponse()
    response.ret = 0
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')

def terminate(request):
    req = request._proto
    f = Friend(request._char_id)
    f.terminate(req.id)

    response = protomsg.FriendTerminateResponse()
    response.ret = 0
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')

def cancel(request):
    req = request._proto
    f = Friend(request._char_id)
    f.cancel(req.id)

    response = protomsg.FriendCancelResponse()
    response.ret = 0
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')

def accept(request):
    req = request._proto
    f = Friend(request._char_id)
    f.accept(req.id)

    response = protomsg.FriendAcceptResponse()
    response.ret = 0
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')

def refuse(request):
    req = request._proto
    f = Friend(request._char_id)
    f.refuse(req.id)

    response = protomsg.FriendRefuseResponse()
    response.ret = 0
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')
