from django.http import HttpResponse

from core.exception import SanguoViewException
from core.formation import save_socket, save_formation
from core import notify
from core.signals import socket_changed_signal

from protomsg import (
        SetFormationResponse,
        SetSocketResponse,
        )

from utils import pack_msg

def set_socket(request):
    req = request._proto
    char_id = request._char_id

    # FIXME request check
    save_socket(
            char_id,
            socket_id=req.socket.id,
            hero=req.socket.hero_id,
            weapon=req.socket.weapon_id,
            armor=req.socket.armor_id,
            jewelry=req.socket.jewelry_id
            )
    
    socket_changed_signal.send(
        sender = None,
        hero = req.socket.hero_id,
        weapon = req.socket.weapon_id,
        armor = req.socket.armor_id,
        jewelry = req.socket.jewelry_id
    )

    response = SetSocketResponse()
    response.ret = 0
    response.socket.MergeFrom(req.socket)
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')



def set_formation(request):
    req = request._proto
    char_id = request._char_id

    socket_ids = req.socket_ids

    if len(socket_ids) != 9:
        raise SanguoViewException(400, "SetFormationResponse")

    save_formation(char_id, [int(s) for s in socket_ids])
    notify.formation_notify('noti:{0}'.format(char_id), char_id, formation=socket_ids)

    response = SetFormationResponse()
    response.ret = 0

    data = pack_msg(response)
    return HttpResponse(data, content_type="text/plain")


