# -*- coding: utf-8 -*-

from mongoengine import DoesNotExist

from core.mongoscheme import MongoSocket, MongoFormation, MongoHero
from core.signals import socket_changed_signal, hero_changed_signal
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

    def max_socket_id(self):
        ids = self.all_socket_ids()
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
        old_formations = self.formation.formation[:]
        for index, sid in enumerate(old_formations):
            if not new_socket_ids:
                break

            if sid == 0:
                self.formation.formation.pop(index)
                self.formation.formation.insert(index, new_socket_ids[0])
                new_socket_ids.pop(0)

        self.formation.save()
        publish_to_char(self.char_id, pack_msg(msg))
        self.send_formation_notify()
        return True


    def set_socket(self, socket_id, hero_id, weapon_id, armor_id, jewelry_id):
        # 由客户端操作来设置socket
        from core.item import Item
        from core.hero import char_heros_dict

        item = Item(self.char_id)

        if str(socket_id) not in self.formation.sockets:
            raise InvalidOperate()

        char_heros = char_heros_dict(self.char_id)

        # 首先检测是否拥有
        if hero_id and hero_id not in char_heros:
            raise InvalidOperate("Formation, Set Socket. Char {0} Try to set hero {1} in socket {2}. But this hero NOT belong to this char".format(
                self.char_id, hero_id, socket_id
            ))

        for i in [weapon_id, armor_id, jewelry_id]:
            if i and not item.has_equip(i):
                raise InvalidOperate("Formation, Set Socket. Char {0} Try to set equip {1} in socket {2}. But this equip NOT belong to this char".format(
                    self.char_id, i, socket_id
                ))

        # 对于第一次上人的情况特殊处理
        this_socket = self.formation.sockets[str(socket_id)]
        if not this_socket.hero and not this_socket.weapon and not this_socket.armor and not this_socket.jewelry and hero_id and not weapon_id and not armor_id and not jewelry_id:
            # first time pick up a hero in this socket
            # 要把这个人往前放
            socket_ids = self.all_socket_ids()
            socket_ids.sort()
            for sid in socket_ids:
                s = self.formation.sockets[str(sid)]
                if not s.hero:
                    self.save_socket(sid, hero_id, s.weapon, s.armor, s.jewelry)
                    return


        # 然后检测装备类型
        def _equip_test(tp, e):
            if not e:
                return

            # 装备类型不能放错
            e_oid = item.item.equipments[str(e)].oid
            this_e = EQUIPMENTS[e_oid]
            if this_e.tp != tp:
                raise SanguoException(402, "Formation, Set Socket. Equip type test Failed. Char {0}. Equip id: {1}, oid {2}, tp {3}. Expect tp: {4}".format(
                    self.char_id, e, e_oid, this_e.tp, tp
                ))

        _equip_test(1, weapon_id)
        _equip_test(2, armor_id)
        _equip_test(3, jewelry_id)


        # 最后检测其他socket
        changed_sockets = []

        off_hero_id = None

        # 不能重复放置
        for k, s in self.formation.sockets.iteritems():
            if int(k) == socket_id:
                if s.hero and s.hero != hero_id:
                    off_hero_id = s.hero
                continue

            if hero_id and s.hero:
                if s.hero == hero_id:
                    # 同一个武将上到多个socket
                    raise SanguoException(401, "Formation, Set Socket. Char {0} Try to set hero {1} in socket {2}. But this hero already in socket {3}".format(
                        self.char_id, hero_id, socket_id, k
                    ))

                # 同名武将不能重复上阵
                if char_heros[s.hero].oid == char_heros[hero_id].oid:
                    raise InvalidOperate("Formation, Set Socket. Char {0} Try to set hero {1} in socket {2}. But Same Hero oid {3} already in socket {4}".format(
                        self.char_id, hero_id, socket_id, char_heros[hero_id].oid, k
                    ))

            if weapon_id and s.weapon and s.weapon == weapon_id:
                changed_sockets.append((int(k), s.hero, 0, s.armor, s.jewelry))

            if armor_id and s.armor and s.armor == armor_id:
                changed_sockets.append((int(k), s.hero, s.weapon, 0, s.jewelry))

            if jewelry_id and s.jewelry and s.jewelry == jewelry_id:
                changed_sockets.append((int(k), s.hero, s.weapon, s.armor, 0))


        self.save_socket(
            socket_id=socket_id,
            hero=hero_id,
            weapon=weapon_id,
            armor=armor_id,
            jewelry=jewelry_id
        )

        for socket_id, hero_id, weapon_id, armor_id, jewelry_id in changed_sockets:
            self.save_socket(
                socket_id=socket_id,
                hero=hero_id,
                weapon=weapon_id,
                armor=armor_id,
                jewelry=jewelry_id,
            )

        if off_hero_id:
            hero_changed_signal.send(
                sender=None,
                hero_id=off_hero_id,
            )


    def save_socket(self, socket_id=None, hero=0, weapon=0, armor=0, jewelry=0, send_notify=True):
        if not socket_id:
            socket_id = self.max_socket_id() + 1
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
        if len(socket_ids) != 9:
            raise InvalidOperate("Formation, Save Formation. Char {0} Try to save formation, But length is {1}. {2}".format(
                self.char_id, len(socket_ids), socket_ids
            ))

        # real_socket_ids = []
        # for i in socket_ids:
        #     if i == 0:
        #         continue
        #     if i not in f.formation.formation:
        #         raise InvalidOperate()
        #     real_socket_ids.append(i)
        #
        # if len(real_socket_ids) != len(f.formation.sockets):
        #     raise InvalidOperate()

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
                raise SanguoException(403, "Formation, Save Formation. Char {0} Try to save formation. But LINE {1} has no hero".format(
                    self.char_id, i
                ))

        all_ids = self.all_socket_ids()
        for _id in socket_ids:
            if _id == 0:
                continue

            if _id not in all_ids:
                raise SanguoException(403, "Formation, Save formation. Char {0} try to set a wrong socket_ids: {1}. Actual: {2}".format(
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

