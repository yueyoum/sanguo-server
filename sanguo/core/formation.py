# -*- coding: utf-8 -*-

from mongoengine import DoesNotExist

from core.mongoscheme import MongoSocket, MongoFormation, MongoHero
from core.signals import socket_changed_signal, hero_changed_signal
from core.exception import SanguoException
from core.attachment import make_standard_drop_from_template
from core.resource import resource_logger

from utils import pack_msg
from core.msgpipe import publish_to_char

import protomsg
from protomsg import SpecialEquipmentBuyRequest

from preset.data import EQUIPMENTS, HEROS
from preset import errormsg

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


TP_TABLE = {
    1: 'weapon',
    2: 'armor',
    3: 'jewelry',
}

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

    def max_socket_id(self):
        ids = self.all_socket_ids()
        if not ids:
            return 0
        return max(ids)

    def opened_socket_amount(self):
        return len(self.formation.sockets)


    def open_socket(self, all_amount):
        # 条件达成自动开启新的socket
        opened = self.opened_socket_amount()
        needed = all_amount - opened
        if needed <= 0:
            return False

        now_id = self.max_socket_id()
        new_socket_ids = []

        msg = protomsg.AddSocketNotify()

        # new socket
        for i in range(needed):
            socket_id = now_id + 1
            socket = MongoSocket()
            socket.hero = 0
            socket.weapon = 0
            socket.armor = 0
            socket.jewelry = 0
            self.formation.sockets[str(socket_id)] = socket

            new_socket_ids.append(socket_id)
            now_id += 1

            msg_s = msg.sockets.add()
            self._msg_socket(msg_s, socket_id, socket)

        # put socket in formation
        for index, sid in enumerate(self.formation.formation):
            if not new_socket_ids:
                break

            if sid == 0:
                self.formation.formation[index] = new_socket_ids[0]
                new_socket_ids.pop(0)

        self.formation.save()
        publish_to_char(self.char_id, pack_msg(msg))
        self.send_formation_notify()
        return True


    def _first_up_hero(self, _socket_id, hero_id):
        # 第一次上人要依次挨着 socket 放置。所以client传来的socket_id无用。
        # 需要自己取出空着的最考前的socket
        socket_id = None
        socket_ids = self.all_socket_ids()
        socket_ids.sort()
        for sid in socket_ids:
            s = self.formation.sockets[str(sid)]
            if not s.hero:
                socket_id = sid
                break

        # XXX
        assert socket_id is not None

        self.formation.sockets[str(socket_id)].hero = hero_id
        self.formation.save()
        self.send_socket_changed_notify(socket_id, self.formation.sockets[str(socket_id)])


    def _replace_hero(self, socket_id, hero_id):
        off_hero = self.formation.sockets[str(socket_id)].hero
        hero_changed_signal.send(
            sender=None,
            hero_id=off_hero,
        )

        self.formation.sockets[str(socket_id)].hero = hero_id
        self.formation.save()

        socket_changed_signal.send(
            sender=None,
            socket_obj=self.formation.sockets[str(socket_id)]
        )

        self.send_socket_changed_notify(socket_id, self.formation.sockets[str(socket_id)])


    def up_hero(self, socket_id, hero_id):
        # 上人
        from core.hero import char_heros_dict

        try:
            this_socket = self.formation.sockets[str(socket_id)]
        except KeyError:
            raise SanguoException(
                errormsg.FORMATION_NONE_EXIST_SOCKET,
                self.char_id,
                "Formation Up Hero",
                "Socket {0} not exist".format(socket_id)
            )

        char_heros = char_heros_dict(self.char_id)
        if hero_id not in char_heros:
            raise SanguoException(
                errormsg.HERO_NOT_EXSIT,
                self.char_id,
                "Formation Up Hero",
                "Set Socket, Hero {0} not belong to self".format(hero_id)
            )


        for k, v in self.formation.sockets.iteritems():
            if int(k) == socket_id:
                continue

            if not v.hero:
                continue

            if v.hero == hero_id:
                # 同一个武将上到多个socket
                raise SanguoException(
                    errormsg.FORMATION_SET_SOCKET_HERO_IN_MULTI_SOCKET,
                    self.char_id,
                    "Formation Up Hero",
                    "Set Socket. hero {0} already in socket {1}".format(hero_id, k)
                )

            # 同名武将不能重复上阵
            if char_heros[v.hero].oid == char_heros[hero_id].oid:
                raise SanguoException(
                    errormsg.FORMATION_SET_SOCKET_SAME_HERO,
                    self.char_id,
                    "Formation Up Hero",
                    "Set Socket. same hero can not in formation at same time"

                )

        if not this_socket.hero:
            # 第一次上人
            self._first_up_hero(socket_id, hero_id)
        else:
            self._replace_hero(socket_id, hero_id)



    def up_equipment(self, socket_id, equipment_id):
        # 上装备
        from core.item import Item

        try:
            this_socket = self.formation.sockets[str(socket_id)]
        except KeyError:
            raise SanguoException(
                errormsg.FORMATION_NONE_EXIST_SOCKET,
                self.char_id,
                "Formation Up Equipment",
                "Socket {0} not exist".format(socket_id)
            )

        item = Item(self.char_id)
        try:
            this_equipment = item.item.equipments[str(equipment_id)]
        except KeyError:
            raise SanguoException(
                errormsg.EQUIPMENT_NOT_EXIST,
                self.char_id,
                "Formation Up Equipment",
                "Set Socket, Equipment {0} not belong to self".format(equipment_id)
            )

        tp = EQUIPMENTS[this_equipment.oid].tp
        tp_name = TP_TABLE[tp]

        setattr(this_socket, tp_name, equipment_id)
        changed_socket = [(socket_id, this_socket)]

        for k, v in self.formation.sockets.iteritems():
            if int(k) == socket_id:
                continue

            if getattr(v, tp_name) == equipment_id:
                setattr(v, tp_name, 0)
                changed_socket.append((int(k), v))
                break

        self.formation.save()

        for k, v in changed_socket:
            self.send_socket_changed_notify(k, v)


    def initialize_socket(self, socket_id=None, hero=0, weapon=0, armor=0, jewelry=0):
        if not socket_id:
            socket_id = self.max_socket_id() + 1
            socket = MongoSocket()
        else:
            try:
                socket = self.formation.sockets[str(socket_id)]
            except KeyError:
                raise SanguoException(
                    errormsg.FORMATION_NONE_EXIST_SOCKET,
                    self.char_id,
                    "Formation Save Socket",
                    "Socket {0} not exist".format(socket_id)
                )

        socket.hero = hero
        socket.weapon = weapon
        socket.armor = armor
        socket.jewelry = jewelry

        self.formation.sockets[str(socket_id)] = socket
        self.formation.save()

        return socket_id


    def save_formation(self, socket_ids, send_notify=True):
        if len(socket_ids) != 9:
            raise SanguoException(
                errormsg.BAD_MESSAGE,
                self.char_id,
                "Formation Save Formation",
                "Save Formation. But request formation length is {0}".format(len(socket_ids))
            )

        request_socket_amount = 0

        all_ids = self.all_socket_ids()
        for _id in socket_ids:
            if _id == 0:
                continue

            if _id not in all_ids:
                raise SanguoException(
                    errormsg.FORMATION_NONE_EXIST_SOCKET,
                    self.char_id,
                    "Formation Save Formation",
                    "Save Formation. {0} not in socket ids {1}".format(_id, all_ids)
                )

            request_socket_amount += 1


        if request_socket_amount != self.opened_socket_amount():
            raise SanguoException(
                errormsg.FORMATION_SOCKET_AMOUNT_NOT_MATCH,
                self.char_id,
                "Formation Save Formation",
                "Save Formation. socket amount not match"
            )

        for i in range(0, 9, 3):
            no_hero = True
            for j in range(3):
                index = i + j
                sid = socket_ids[index]
                if sid == 0:
                    continue
                s = self.formation.sockets[str(sid)]
                if s.hero:
                    no_hero = False
                    break
            if no_hero:
                raise SanguoException(
                    errormsg.FORMATION_SAVE_NO_HERO,
                    self.char_id,
                    "Formation Save Formation",
                    "Save Formation. Line {0} has no hero".format(i)
                )

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
        from core.hero import char_heros_dict

        ids = self.in_formation_hero_ids()
        char_heros = char_heros_dict(self.char_id)

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
        # FIXME
        try:
            this_socket = self.formation.sockets[str(socket_id)]
        except KeyError:
            raise SanguoException(
                errormsg.FORMATION_NONE_EXIST_SOCKET,
                self.char_id,
                "Formation Special Buy",
                "socket {0} not exist".format(socket_id)
            )

        if not this_socket.hero:
            raise SanguoException(
                errormsg.FORMATION_NO_HERO,
                self.char_id,
                "Formation Special Buy",
                "socket {0} no hero".format(socket_id)
            )


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

        standard_drop = make_standard_drop_from_template()
        standard_drop['equipments'] = [(new_id, 1, 1)]
        standard_drop['income'] = 1
        standard_drop['func_name'] = "Special Buy"
        standard_drop['des'] = ''
        resource_logger(self.char_id, standard_drop)

        self.send_socket_changed_notify(socket_id, self.formation.sockets[str(socket_id)])


    def send_socket_changed_notify(self, socket_id, socket):
        msg = protomsg.UpdateSocketNotify()
        s = msg.sockets.add()
        self._msg_socket(s, socket_id, socket)
        publish_to_char(self.char_id, pack_msg(msg))

        socket_changed_signal.send(
            sender=None,
            socket_obj=socket
        )


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

