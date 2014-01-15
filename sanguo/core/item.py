# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/14/14'

from mongoengine import DoesNotExist

from apps.item.models import Equipment as MysqlEquipment
from core.mongoscheme import MongoItem, MongoEmbeddedEquipment
from core.drives import document_ids

from core.exception import InvalidOperate, GoldNotEnough
from core.msgpipe import publish_to_char
from core.character import Char

from utils import pack_msg

import protomsg


class Equipment(object):
    def __init__(self, char_id=None, equip_id=None, oid=None, level=None, gems=None):
        if char_id and equip_id:
            mi = MongoItem.objects.only('equipments').get(id=char_id)
            equip = mi.equipments[str(equip_id)]
            self.oid = equip.oid
            self.level = equip.level
            self.gems = equip.gems
        else:
            if oid is None or level is None:
                raise Exception("Equipment, Bad Arguments")

            self.oid = oid
            self.level = level
            self.gems = gems if gems else []

        all_equips = MysqlEquipment.all()
        self.equip = all_equips[self.oid]


    def sell_gold(self):
        # 出售价格 金币
        total_gold = 100 * (1 - pow(1.08, self.level)) / (1 - 1.08)
        return int(total_gold * 0.9)

    def level_up_need_gold(self):
        # 强化升级所需金币
        gold = pow(1.08, self.level) * 100
        return int(gold)

    @property
    def attack(self):
        if not self.equip.attack:
            return 0

        return self.equip.attack + self.level * self.equip.growing

    @property
    def defense(self):
        if not self.equip.defense:
            return 0

        return self.equip.defense + self.level * self.equip.growing

    @property
    def hp(self):
        if not self.equip.hp:
            return 0

        return self.equip.hp + self.level * self.equip.growing




class Item(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.item = MongoItem.objects.get(id=self.char_id)
        except DoesNotExist:
            self.item = MongoItem(id=self.char_id)
            self.item.save()

    def has_equip(self, equip_id):
        return str(equip_id) in self.item.equipments

    def equip_add(self, oid, level=1, notify=True):
        # TODO 背包是否满了
        new_id = document_ids.inc('equipment')
        me = MongoEmbeddedEquipment()
        me.oid = oid
        me.level = level
        me.gems = []

        self.item.equipments[str(new_id)] = me
        self.item.save()

        if notify:
            msg = protomsg.AddEquipNotify()
            msg_equip = msg.equips.add()
            self._msg_equip(msg_equip, new_id, oid, level, [])
            publish_to_char(self.char_id, pack_msg(msg))

        return new_id

    def equip_remove(self, _id):
        try:
            del self.item.equipments[str(_id)]
        except KeyError:
            raise InvalidOperate()

        self.item.save()

        msg = protomsg.RemoveEquipNotify()
        msg.ids.append(_id)
        publish_to_char(self.char_id, pack_msg(msg))


    def equip_level_up(self, _id):
        try:
            equip = self.item.equipments[str(_id)]
        except KeyError:
            raise InvalidOperate()

        if equip.level >= 99:
            raise InvalidOperate()

        e = Equipment(oid=equip.oid, level=equip.level)
        gold_needs = e.level_up_need_gold()

        char = Char(self.char_id)
        cache_char = char.cacheobj
        if cache_char.gold < gold_needs:
            raise GoldNotEnough()

        char.update(gold=-gold_needs)
        self.item.equipments[str(_id)].level += 1
        self.item.save()

        self._equip_update_notify(_id, self.item.equipments[str(_id)])


    def equip_step_up(self, _id, to):
        # TODO check stuffs
        try:
            equip = self.item.equipments[str(_id)]
        except KeyError:
            raise InvalidOperate()

        all_equips = MysqlEquipment.all()
        this_equip = all_equips[_id]

        to_oids = [int(i) for i in this_equip.upgrade_to.split(',')]
        if to not in to_oids:
            raise InvalidOperate()

        self.item.equipments[str(_id)].oid = to
        self.item.save()

        self._equip_update_notify(_id, self.item.equipments[str(_id)])


    def equip_sell(self, _id):
        if not self.has_equip(_id):
            raise InvalidOperate()

        e = Equipment(char_id=self.char_id, equip_id=_id)
        gold = e.sell_gold()
        char = Char(self.char_id)
        char.update(gold=gold)

        self.equip_remove(_id)

    def equip_embed(self, _id, slot_id, gem_id):
        pass

    def equip_unembed(self, _id, slot_id):
        pass

    def gem_merge(self, _id):
        pass


    def _msg_equip(self, msg, _id, oid, level, gems):
        msg.id = _id
        msg.oid = oid
        msg.level = level

        equip = Equipment(oid=oid, level=level)
        msg.level_up_need_gold = equip.level_up_need_gold()
        msg.attack = equip.attack
        msg.defense = equip.defense
        msg.hp = equip.hp
        msg.gem_ids.extend(gems)
        msg.sell_gold = 0

    def _equip_update_notify(self, _id, equip):
        msg = protomsg.UpdateEquipNotify()
        msg_equip = msg.equips.add()
        self._msg_equip(msg_equip, _id, equip.oid, equip.level, equip.gems)
        publish_to_char(self.char_id, pack_msg(msg))

    def send_equip_notify(self):
        msg = protomsg.EquipNotify()
        for _id, data in self.item.equipments.iteritems():
            equip = msg.equips.add()
            self._msg_equip(equip, int(_id), data.oid, data.level, data.gems)

        publish_to_char(self.char_id, pack_msg(msg))
