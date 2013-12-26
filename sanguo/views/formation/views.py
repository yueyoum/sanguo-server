# -*- coding: utf-8 -*-
from django.http import HttpResponse

from apps.item.cache import get_cache_equipment
from core.character import Char
from core.exception import InvalidOperate, SanguoViewException
from core.mongoscheme import MongoChar
from protomsg import SetFormationResponse, SetSocketResponse
from utils import pack_msg


def set_socket(request):
    req = request._proto
    char_id = request._char_id
    
    char = Char(char_id)
    char_eqiup_ids = char.equip_ids
    char_heros = char.heros_dict
    
    mc = MongoChar.objects.only('sockets').get(id=char_id)
    char_sockets = mc.sockets
    
    if str(req.socket.id) not in char_sockets:
        # socket id 要存在
        raise InvalidOperate("SetSocketResponse")
    
    # 不能重复放置
    for k, s in char_sockets.iteritems():
        if int(k) == req.socket.id:
            continue

        if req.socket.hero_id:
            if s.hero and s.hero == req.socket.hero_id:
                raise SanguoViewException(401, "SetSocketResponse")
        
        if req.socket.weapon_id:
            if s.weapon and s.weapon == req.socket.weapon_id:
                char_sockets[k].weapon = 0
        
        if req.socket.armor_id:
            if s.armor and s.armor == req.socket.armor_id:
                char_sockets[k].armor = 0
        
        if req.socket.jewelry_id:
            if s.jewelry and s.jewelry == req.socket.jewelry_id:
                char_sockets[k].jewelry = 0
    
    mc.save()

    if req.socket.hero_id:
        # hero 要属于这个char
        if req.socket.hero_id not in char_heros:
            raise InvalidOperate("SetSocketResponse")
        
    
    def _equip_test(tp, e):
        if e:
            # 装备要有，类型不能放错
            if e not in char_eqiup_ids:
                raise InvalidOperate("SetSocketResponse")
            obj = get_cache_equipment(e)
            if obj.tp != tp:
                raise SanguoViewException(402, "SetSocketResponse")
    
    _equip_test(1, req.socket.weapon_id)
    _equip_test(2, req.socket.jewelry_id)
    _equip_test(3, req.socket.armor_id)

    char.save_socket(
            socket_id=req.socket.id,
            hero=req.socket.hero_id,
            weapon=req.socket.weapon_id,
            armor=req.socket.armor_id,
            jewelry=req.socket.jewelry_id
            )
    
    response = SetSocketResponse()
    response.ret = 0
    response.socket.MergeFrom(req.socket)
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')



def set_formation(request):
    req = request._proto
    char_id = request._char_id
    
    char = Char(char_id)
    char_sockets = char.sockets
    socket_ids = [int(s) for s in req.socket_ids]

    if len(socket_ids) != 9:
        raise SanguoViewException(400, "SetFormationResponse")


    real_socket_ids = []
    for i in socket_ids:
        if i == 0:
            continue
        if i not in char_sockets:
            raise InvalidOperate("SetFormationResponse")
        real_socket_ids.append(i)
    
    if len(real_socket_ids) != len(char_sockets):
        raise SanguoViewException(400, "SetFormationResponse")
    
    for i in range(0, 9, 3):
        no_hero = True
        for j in range(3):
            index = i + j
            sid = socket_ids[index]
            if sid == 0:
                continue
            s = char_sockets[socket_ids[index]]
            if s.hero:
                no_hero = False
                break
        if no_hero:
            raise SanguoViewException(403, "SetFormationResponse")
            
    
    char.save_formation(socket_ids)

    response = SetFormationResponse()
    response.ret = 0
    data = pack_msg(response)
    return HttpResponse(data, content_type="text/plain")
