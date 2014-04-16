# -*- coding: utf-8 -*-

from core.formation import Formation
from utils.decorate import message_response

@message_response("SetSocketResponse")
def set_socket(request):
    req = request._proto
    char_id = request._char_id
    f = Formation(char_id)

    f.set_socket(
        socket_id=req.socket.id,
        hero_id=req.socket.hero_id,
        weapon_id=req.socket.weapon_id,
        armor_id=req.socket.armor_id,
        jewelry_id=req.socket.jewelry_id
    )

    return None


@message_response("SetFormationResponse")
def set_formation(request):
    req = request._proto
    char_id = request._char_id

    f = Formation(char_id)

    socket_ids = [int(s) for s in req.socket_ids]
    f.save_formation(socket_ids)
    return None
