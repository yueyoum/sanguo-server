# -*- coding: utf-8 -*-

from core.character import Char
from core.exception import InvalidOperate, SanguoException
from protomsg import SetSocketResponse
from utils import pack_msg
from utils.decorate import message_response

from core.formation import Formation
from core.item import Item

@message_response("SetSocketResponse")
def set_socket(request):
    req = request._proto
    char_id = request._char_id

    item = Item(char_id)
    f = Formation(char_id)

    if str(req.socket.id) not in f.formation.sockets:
        raise InvalidOperate()
    #
    char = Char(char_id)
    # char_eqiup_ids = char.equip_ids
    char_heros = char.heros_dict
    #
    # mc = MongoChar.objects.only('sockets').get(id=char_id)
    # char_sockets = mc.sockets
    #
    # if str(req.socket.id) not in char_sockets:
    #     # socket id 要存在
    #     raise InvalidOperate()

    if req.socket.hero_id:
        # hero 要属于这个char
        if req.socket.hero_id not in char_heros:
            raise InvalidOperate()

    # 不能重复放置
    for k, s in f.formation.sockets.iteritems():
        if int(k) == req.socket.id:
            continue

        if req.socket.hero_id:
            if s.hero and s.hero == req.socket.hero_id:
                raise SanguoException(401)

        if req.socket.weapon_id:
            if s.weapon and s.weapon == req.socket.weapon_id:
                f.formation.sockets[k].weapon = 0

        if req.socket.armor_id:
            if s.armor and s.armor == req.socket.armor_id:
                f.formation.sockets[k].armor = 0

        if req.socket.jewelry_id:
            if s.jewelry and s.jewelry == req.socket.jewelry_id:
                f.formation.sockets[k].jewelry = 0


    def _equip_test(tp, e):
        if e:
            # 装备要有，类型不能放错
            if not item.has_equip(e):
                raise InvalidOperate()
            # TODO tp check
            # obj = get_cache_equipment(e)
            # if obj.tp != tp:
            #     raise SanguoException(402)

    _equip_test(1, req.socket.weapon_id)
    _equip_test(2, req.socket.jewelry_id)
    _equip_test(3, req.socket.armor_id)


    f.save_socket(
        socket_id=req.socket.id,
        hero=req.socket.hero_id,
        weapon=req.socket.weapon_id,
        armor=req.socket.armor_id,
        jewelry=req.socket.jewelry_id
    )
    f.formation.save()

    response = SetSocketResponse()
    response.ret = 0
    response.socket.MergeFrom(req.socket)
    return pack_msg(response)


@message_response("SetFormationResponse")
def set_formation(request):
    req = request._proto
    char_id = request._char_id

    f = Formation(char_id)

    socket_ids = [int(s) for s in req.socket_ids]

    print socket_ids
    if len(socket_ids) != 9:
        raise InvalidOperate()

    print f.formation.formation

    real_socket_ids = []
    for i in socket_ids:
        if i == 0:
            continue
        if i not in f.formation.formation:
            raise InvalidOperate()
        real_socket_ids.append(i)

    print "XXX"
    print real_socket_ids
    print f.formation.sockets
    if len(real_socket_ids) != len(f.formation.sockets):
        raise InvalidOperate()

    print "YYY"
    for i in range(0, 9, 3):
        no_hero = True
        for j in range(3):
            index = i + j
            sid = socket_ids[index]
            if sid == 0:
                continue
            s = f.formation.sockets[str(socket_ids[index])]
            if s.hero:
                no_hero = False
                break
        if no_hero:
            raise SanguoException(403)

    f.save_formation(socket_ids)
    return None
