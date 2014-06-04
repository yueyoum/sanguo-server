# -*- coding: utf-8 -*-

from core.formation import Formation
from utils.decorate import message_response


@message_response("SetSocketHeroResponse")
def up_hero(request):
    req = request._proto
    char_id = request._char_id

    f = Formation(char_id)
    f.up_hero(req.socket_id, req.hero_id)


@message_response("SetSocketEquipmentResponse")
def up_equipment(request):
    req = request._proto
    char_id = request._char_id

    f = Formation(char_id)
    f.up_equipment(req.socket_id, req.equipment_id)



@message_response("SetFormationResponse")
def set_formation(request):
    req = request._proto
    char_id = request._char_id

    f = Formation(char_id)

    socket_ids = [int(s) for s in req.socket_ids]
    f.save_formation(socket_ids)
