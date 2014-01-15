# -*- coding: utf-8 -*-

from mongoengine import DoesNotExist
from core.mongoscheme import MongoSocket, MongoFormation
from core.signals import formation_changed_signal, socket_changed_signal
from core.exception import InvalidOperate

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

        if socket.hero and send_notify:
            equip_ids = []
            if socket.weapon:
                equip_ids.append(socket.weapon)
            if socket.armor:
                equip_ids.append(socket.armor)
            if socket.jewelry:
                equip_ids.append(socket.jewelry)

            if equip_ids:
                socket_changed_signal.send(
                    sender=None,
                    hero=socket.hero,
                    equip_ids=equip_ids
                )

        return socket_id


    def save_formation(self, socket_ids, send_notify=True):
        # TODO check
        self.formation.formation = socket_ids
        self.formation.save()

        if send_notify:
            formation_changed_signal.send(
                sender=None,
                char_id=self.char_id,
                socket_ids=socket_ids
            )



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


    def send_socket_notify(self):
        msg = protomsg.SocketNotify()
        for k, v in self.formation.sockets.iteritems():
            s = msg.sockets.add()
            s.id = int(k)
            s.hero_id = v.hero or 0
            s.weapon_id = v.weapon or 0
            s.armor_id = v.armor or 0
            s.jewelry_id = v.jewelry or 0

        publish_to_char(self.char_id, pack_msg(msg))


    def send_formation_notify(self):
        msg = protomsg.FormationNotify()
        msg.socket_ids.extend(self.formation.formation)
        publish_to_char(self.char_id, pack_msg(msg))





