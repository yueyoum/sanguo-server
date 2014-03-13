# -*- coding: utf-8 -*-

from mongoengine import DoesNotExist
from core.mongoscheme import MongoSocket, MongoFormation
from core.signals import socket_changed_signal
from core.exception import InvalidOperate, SanguoException

from utils import pack_msg
from core.msgpipe import publish_to_char

import protomsg


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

    def save_socket(self, socket_id=None, hero=0, weapon=0, armor=0, jewelry=0, send_notify=True):
        if not socket_id:
            socket_id = len(self.formation.sockets) + 1
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

            msg = protomsg.SocketNotify()
            s = msg.sockets.add()
            self._msg_socket(s, socket_id, socket)
            publish_to_char(self.char_id, pack_msg(msg))

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
        for s in self.formation.sockets.values():
            if s.hero:
                hero_ids.append(s.hero)
        return hero_ids



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





