# -*- coding: utf-8 -*-

from mongoengine import DoesNotExist

from core.mongoscheme import MongoSocket, MongoFormation, MongoHero
from core.signals import socket_changed_signal
from core.exception import InvalidOperate, SanguoException

from utils import pack_msg
from core.msgpipe import publish_to_char

import protomsg
from protomsg import SpecialEquipmentBuyRequest

from preset.data import EQUIPMENTS, HEROS

ALL_INITIAL_EQUIPMENTS = {}

for d in EQUIPMENTS.values():
    if d.step == 0:
        ALL_INITIAL_EQUIPMENTS[d.id] = d

ALL_WEAPONS = {}
ALL_ARMORS = {}
ALL_JEWELRY = {}
for _e in EQUIPMENTS.values():
    if _e.tp == 1:
        ALL_WEAPONS[_e.id] = _e
    elif _e.tp == 2:
        ALL_ARMORS[_e.id] = _e
    else:
        ALL_JEWELRY[_e.id] = _e



class Formation(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.formation = MongoFormation.objects.get(id=self.char_id)
        except DoesNotExist:
            self.formation = MongoFormation(id=self.char_id)
            self.formation.formation = [0] * 9
            self.formation.save()

    def all_socket_ids(self):
        ids = self.formation.sockets.keys()
        return [int(i) for i in ids]

    def opened_socket_amount(self):
        return len(self.formation.sockets)


    def open_socket(self, all_amount):
        opened = self.opened_socket_amount()
        needed = all_amount - opened
        if needed <= 0:
            return

        msg = protomsg.AddSocketNotify()

        for i in range(needed):
            socket_id = self.opened_socket_amount() + 1
            socket = MongoSocket()
            socket.hero = 0
            socket.weapon = 0
            socket.armor = 0
            socket.jewelry = 0
            self.formation.sockets[str(socket_id)] = socket

            msg_s = msg.sockets.add()
            self._msg_socket(msg_s, socket_id, socket)

        self.formation.save()
        publish_to_char(self.char_id, pack_msg(msg))



    def save_socket(self, socket_id=None, hero=0, weapon=0, armor=0, jewelry=0, send_notify=True):
        if not socket_id:
            socket_id = self.opened_socket_amount() + 1
            socket = MongoSocket()
        else:
            try:
                socket = self.formation.sockets[str(socket_id)]
            except KeyError:
                raise InvalidOperate()

        socket.hero = hero
        socket.weapon = weapon
        socket.armor = armor
        socket.jewelry = jewelry

        self.formation.sockets[str(socket_id)] = socket
        self.formation.save()

        if send_notify:
            socket_changed_signal.send(
                sender=None,
                socket_obj=socket
            )

            self._send_socket_changed_notify(socket_id, socket)

        return socket_id


    def save_formation(self, socket_ids, send_notify=True):
        all_ids = self.all_socket_ids()
        for _id in socket_ids:
            if _id == 0:
                continue

            if _id not in all_ids:
                raise SanguoException(403, "Formation Set formation. Char {0} try to set a wrong socket_ids: {1}. Actual: {2}".format(
                    self.char_id, socket_ids, all_ids
                ))

        self.formation.formation = socket_ids
        self.formation.save()

        if send_notify:
            self.send_formation_notify()

    def in_formation_hero_ids(self):
        hero_ids = []
        sockets = self.formation.sockets
        for sid in self.formation.formation:
            if sid == 0:
                hero_ids.append(0)
                continue

            s = sockets[str(sid)]
            if s.hero:
                hero_ids.append(s.hero)
            else:
                hero_ids.append(0)
        return hero_ids


    def in_formation_hero_original_ids(self):
        from core.character import Char
        ids = self.in_formation_hero_ids()

        char = Char(self.char_id)
        char_heros = char.heros_dict

        res = []
        for i in ids:
            if i == 0:
                res.append(0)
            else:
                res.append(char_heros[i].oid)

        return res


    def find_socket_by_hero(self, hero_id):
        for k, v in self.formation.sockets.iteritems():
            if v.hero == hero_id:
                return v
        return None


    def find_socket_by_equip(self, equip_id):
        for k, v in self.formation.sockets.iteritems():
            if v.weapon == equip_id or v.armor == equip_id or v.jewelry == equip_id:
                return v
        return None


    def special_buy(self, socket_id, tp):
        try:
            this_socket = self.formation.sockets[str(socket_id)]
        except KeyError:
            raise InvalidOperate("Formation Special Buy. Char {0} try to operate on a NONE exists socket id {1}".format(self.char_id, socket_id))

        if not this_socket.hero:
            raise InvalidOperate("Formation Special Buy. Char {0}. Can NOT buy special equipment for socket {1} which has no hero".format(
                self.char_id, socket_id
            ))

        oid = MongoHero.objects.get(id=this_socket.hero).oid

        this_hero = HEROS[oid]
        special_cls = [int(i) for i in this_hero.special_equip_cls.split(',')]

        def _find_speicial_id(equipments):
            for e in equipments:
                if e.step == 0 and e.cls in special_cls:
                    return e.id

            # FIXME
            raise Exception("Special buy, not find. tp = {0}".format(tp))

        from core.item import Item
        item = Item(self.char_id)

        if tp == SpecialEquipmentBuyRequest.SOCKET_WEAPON:
            on_id = _find_speicial_id(ALL_WEAPONS.values())
            new_id = item.equip_add(on_id)
            self.formation.sockets[str(socket_id)].weapon = new_id
        elif tp == SpecialEquipmentBuyRequest.SOCKET_ARMOR:
            on_id = _find_speicial_id(ALL_ARMORS.values())
            new_id = item.equip_add(on_id)
            self.formation.sockets[str(socket_id)].armor = new_id
        else:
            on_id = _find_speicial_id(ALL_JEWELRY.values())
            new_id = item.equip_add(on_id)
            self.formation.sockets[str(socket_id)].jewelry = new_id

        self.formation.save()
        socket_changed_signal.send(
            sender=None,
            socket_obj=self.formation.sockets[str(socket_id)]
        )

        self._send_socket_changed_notify(socket_id, self.formation.sockets[str(socket_id)])


    def _send_socket_changed_notify(self, socket_id, socket):
        msg = protomsg.UpdateSocketNotify()
        s = msg.sockets.add()
        self._msg_socket(s, socket_id, socket)
        publish_to_char(self.char_id, pack_msg(msg))


    def _msg_socket(self, msg, _id, socket):
        msg.id = _id
        msg.hero_id = socket.hero or 0
        msg.weapon_id = socket.weapon or 0
        msg.armor_id = socket.armor or 0
        msg.jewelry_id = socket.jewelry or 0


    def send_socket_notify(self):
        msg = protomsg.SocketNotify()
        for k, v in self.formation.sockets.iteritems():
            s = msg.sockets.add()
            self._msg_socket(s, int(k), v)

        publish_to_char(self.char_id, pack_msg(msg))


    def send_formation_notify(self):
        msg = protomsg.FormationNotify()
        msg.socket_ids.extend(self.formation.formation)
        publish_to_char(self.char_id, pack_msg(msg))

