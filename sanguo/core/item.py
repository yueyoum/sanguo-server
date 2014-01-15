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
        return int(total_gold * 0.7)

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

    def has_gem(self, gem_id):
        return str(gem_id) in self.item.gems

    def equip_add(self, oid, level=1, notify=True):
        # TODO 背包是否满了
        this_equip = MysqlEquipment.all()[oid]
        new_id = document_ids.inc('equipment')
        me = MongoEmbeddedEquipment()
        me.oid = oid
        me.level = level
        me.gems = [0] * this_equip.slots

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
        if not self.has_equip(_id):
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
        # gem_id = 0 表示取下slot_id对应的宝石
        if not self.has_equip(_id):
            raise InvalidOperate()

        if gem_id and not self.has_gem(gem_id):
            raise InvalidOperate()

        slot_index = slot_id - 1
        this_equip = self.item.equipments[str(_id)]
        try:
            off_gem = this_equip.gems[slot_index]
            this_equip.gems[slot_index] = gem_id
        except IndexError:
            raise InvalidOperate()

        if gem_id:
            # 镶嵌
            self.gem_remove(gem_id, 1)
            if off_gem:
                self.gem_add([(off_gem, 1)])
        else:
            # 取下
            if not off_gem:
                raise InvalidOperate()
            self.gem_add([(off_gem, 1)])

        self.item.save()
        self._equip_update_notify(_id, this_equip)


    def gem_add(self, add_gems):
        """

        @param add_gems: [(id, amount), (id, amount)]
        @type add_gems: list | tuple
        """
        gems = self.item.gems
        add_gems_dict = {}
        for gid, amount in add_gems:
            add_gems_dict[gid] = add_gems_dict.get(gid, 0) + amount

        new_gems = []
        update_gems = []
        for gid, amount in add_gems_dict.iteritems():
            gid = str(gid)
            if gid in gems:
                gems[gid] += amount
                update_gems.append((int(gid), gems[gid]))
            else:
                gems[gid] = amount
                new_gems.append((int(gid), amount))

        self.item.gems = gems
        self.item.save()

        if new_gems:
            msg = protomsg.AddGemNotify()
            for k, v in new_gems:
                g = msg.gems.add()
                g.id, g.amount = k, v

            publish_to_char(self.char_id, pack_msg(msg))

        if update_gems:
            msg = protomsg.UpdateGemNotify()
            for k, v in update_gems:
                g = msg.gems.add()
                g.id, g.amount = k, v

            publish_to_char(self.char_id, pack_msg(msg))

    def gem_remove(self, _id, amount):
        """

        @param _id: gem id
        @type _id: int
        @param amount: this gem amount
        @type amount: int
        """
        try:
            this_gem_amount = self.item.gems[str(_id)]
        except KeyError:
            raise InvalidOperate()

        new_amount = this_gem_amount - amount
        if new_amount <= 0:
            self.item.gems.pop(str(_id))
            self.item.save()

            msg = protomsg.RemoveGemNotify()
            msg.ids.append(_id)
            publish_to_char(self.char_id, pack_msg(msg))
        else:
            self.item.gems[str(_id)] = new_amount
            self.item.save()
            msg = protomsg.UpdateGemNotify()
            g = msg.gems.add()
            g.id, g.amount = _id, new_amount

            publish_to_char(self.char_id, pack_msg(msg))

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


    def send_gem_notify(self):
        msg = protomsg.GemNotify()
        for k, v in self.item.gems.iteritems():
            g = msg.gems.add()
            g.id, g.amount = int(k), v

        publish_to_char(self.char_id, pack_msg(msg))


    def send_notify(self):
        self.send_equip_notify()
        self.send_gem_notify()