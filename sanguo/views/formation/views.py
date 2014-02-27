# -*- coding: utf-8 -*-

from apps.item.models import Equipment as ModelEquipment
from core.mongoscheme import MongoHero, MongoItem
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

    char = Char(char_id)
    char_heros = char.heros_dict

    if req.socket.hero_id:
        # hero 要属于这个char
        if req.socket.hero_id not in char_heros:
            raise InvalidOperate()

    def _get_hero_oid(hid):
        h = MongoHero.objects.get(id=hid)
        return h.oid

    # 不能重复放置
    for k, s in f.formation.sockets.iteritems():
        if int(k) == req.socket.id:
            continue

        if req.socket.hero_id:
            if s.hero and s.hero == req.socket.hero_id:
                raise SanguoException(401)
            # 同名武将不能重复上阵
            if s.hero:
                if _get_hero_oid(s.hero) == _get_hero_oid(req.socket.hero_id):
                    raise InvalidOperate("Same Hero can not in formation at same time")

        if req.socket.weapon_id:
            if s.weapon and s.weapon == req.socket.weapon_id:
                f.formation.sockets[k].weapon = 0

        if req.socket.armor_id:
            if s.armor and s.armor == req.socket.armor_id:
                f.formation.sockets[k].armor = 0

        if req.socket.jewelry_id:
            if s.jewelry and s.jewelry == req.socket.jewelry_id:
                f.formation.sockets[k].jewelry = 0

    all_equipments = ModelEquipment.all()
    def _equip_test(tp, e):
        if e:
            # 装备要有，类型不能放错
            if not item.has_equip(e):
                raise InvalidOperate()
            e_oid = item.item.equipments[str(e)].oid
            this_e = all_equipments[e_oid]
            if this_e.tp != tp:
                raise SanguoException(402)

    _equip_test(1, req.socket.weapon_id)
    _equip_test(2, req.socket.armor_id)
    _equip_test(3, req.socket.jewelry_id)


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

    if len(socket_ids) != 9:
        raise InvalidOperate()


    real_socket_ids = []
    for i in socket_ids:
        if i == 0:
            continue
        if i not in f.formation.formation:
            raise InvalidOperate()
        real_socket_ids.append(i)


    if len(real_socket_ids) != len(f.formation.sockets):
        raise InvalidOperate()

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
