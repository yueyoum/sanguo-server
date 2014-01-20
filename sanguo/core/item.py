# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/14/14'

from mongoengine import DoesNotExist

from apps.item.models import Equipment as ModelEquipment
from apps.item.models import Gem as MysqlGem
from core.mongoscheme import MongoItem, MongoEmbeddedEquipment
from core.drives import document_ids

from core.exception import InvalidOperate, GoldNotEnough, GemNotEnough
from core.msgpipe import publish_to_char
from core.character import Char
from core.signals import equip_changed_signal

from utils import pack_msg
from utils import cache

import protomsg

#
# def _save_cache_equipment(equip_obj):
#     cache.set('equip:{0}'.format(equip_obj.equip_id), equip_obj)

def equip_updated(func):
    def deco(self, *args, **kwargs):
        res = func(self, *args, **kwargs)
        # _save_cache_equipment(self)
        self.send_update_notify()
        equip_changed_signal.send(
            sender=None,
            char_id=self.char_id,
            equip_obj=self
        )
        return res
    return deco


class MessageEquipmentMixin(object):
    def _msg_equip(self, msg, _id, mongo_equip, equip_obj):
        """

        @param msg: one equip message
        @type msg: protomsg.Equipment
        @param _id: equip id
        @type _id: int
        @param mongo_equip: mongo equip object
        @type mongo_equip: MongoEmbeddedEquipment
        @param equip_obj: Equipment obj
        @type equip_obj: Equipment
        """
        msg.id = _id
        msg.oid = mongo_equip.oid
        msg.level = mongo_equip.level

        msg.level_up_need_gold = equip_obj.level_up_need_gold()
        msg.attack = equip_obj.attack
        msg.defense = equip_obj.defense
        msg.hp = equip_obj.hp
        msg.gem_ids.extend(mongo_equip.gems)
        msg.sell_gold = equip_obj.sell_gold()



class Equipment(MessageEquipmentMixin):
    def __init__(self, char_id, equip_id, mongo_item_obj=None):
        self.char_id = char_id
        self.equip_id = equip_id

        if mongo_item_obj:
            self.mongo_item = mongo_item_obj
        else:
            self.mongo_item = MongoItem.objects.only('equipments').get(id=char_id)

        mongo_equip = self.mongo_item.equipments[str(equip_id)]
        self.oid = mongo_equip.oid
        self.level = mongo_equip.level

        all_equips = ModelEquipment.all()
        self.equip = all_equips[self.oid]

    # @staticmethod
    # def cache_obj(equip_id):
    #     e = cache.get('equip:{0}'.format(equip_id))
    #     if e:
    #         return e

    @equip_updated
    def level_up(self):
        if self.level >= 99:
            raise InvalidOperate("Equipment Level Up. Char {0} Try Level Up Equipment {1}. But Equipment already level {2}".format(
                self.char_id, self.equip_id, self.level
            ))

        gold_needs = self.level_up_need_gold()
        char = Char(self.char_id)
        cache_char = char.cacheobj
        if cache_char.gold < gold_needs:
            raise GoldNotEnough("Equipment Level Up. Char {0} Gold {1} Not Enough. Needs {2}".format(
                self.char_id, cache_char.gold, gold_needs
            ))

        char.update(gold=-gold_needs)
        self.mongo_item.equipments[str(self.equip_id)].level += 1
        self.mongo_item.save()
        self.level += 1

    @equip_updated
    def step_up(self, to):
        # XXX 在调用之前要检查材料是否足够
        to_oids = [int(i) for i in self.equip.upgrade_to.split(',')]
        if to not in to_oids:
            raise InvalidOperate("Equipment Step Up: Char {0} Try to Up Equipment {1} to {2}".format(
                self.char_id, self.equip_id, to
            ))

        new_equip = ModelEquipment.all()[to]

        self.mongo_item.equipments[str(self.equip_id)].oid = to
        add_gem_slots = new_equip.slots - len(self.mongo_item.equipments[str(self.equip_id)].gems)
        # TODO check this value
        for i in range(add_gem_slots):
            self.mongo_item.equipments[str(self.equip_id)].gems.append(0)

        self.mongo_item.save()
        self.oid = to


    @equip_updated
    def add_gem(self, index, gem_id):
        try:
            off_gem = self.mongo_item.equipments[str(self.equip_id)].gems[index]
            self.mongo_item.equipments[str(self.equip_id)].gems[index] = gem_id
        except IndexError:
            raise InvalidOperate("Equipment Add Gem: Char {0} Try to add gem to a NONE exist gem slot. Equipment: {1}, Gems {2}".format(
                self.char_id, self.equip_id, self.mongo_item.equipments[str(self.equip_id)].gems
            ))

        self.mongo_item.save()
        return off_gem

    @equip_updated
    def rem_gem(self, index):
        try:
            off_gem = self.mongo_item.equipments[str(self.equip_id)].gems[index]
            self.mongo_item.equipments[str(self.equip_id)].gems[index] = 0
        except IndexError:
            raise InvalidOperate("Equipment Add Gem: Char {0} Try to remove gem from a NONE exist gem slot. Equipment: {1}, Gems {2}".format(
                self.char_id, self.equip_id, self.mongo_item.equipments[str(self.equip_id)].gems
            ))

        self.mongo_item.save()
        return off_gem


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


    @property
    def gem_attributes(self):
        attrs = {}

        gems = self.mongo_item.equipments[str(self.equip_id)].gems
        all_gems = MysqlGem.all()
        # TODO get gem
        for gid in gems:
            if not gid:
                continue
            gem = all_gems[gid]
            attrs[gem.used_for] = attrs.get(gem.used_for, 0) + gem.value

        for k, v in attrs.iteritems():
            attrs[k] *= (1 + self.equip.gem_addition / 100.0)

        return attrs

    def send_update_notify(self):
        msg = protomsg.UpdateEquipNotify()
        msg_equip = msg.equips.add()
        self._msg_equip(msg_equip, self.equip_id, self.mongo_item.equipments[str(self.equip_id)], self)
        publish_to_char(self.char_id, pack_msg(msg))



class Item(MessageEquipmentMixin):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.item = MongoItem.objects.get(id=self.char_id)
        except DoesNotExist:
            self.item = MongoItem(id=self.char_id)
            self.item.save()

    def has_equip(self, equip_id):
        return str(equip_id) in self.item.equipments

    def has_gem(self, gem_id, amount=1):
        return self.item.gems.get(str(gem_id), 0) >= amount

    def has_stuff(self, stuff_id, amount=1):
        return self.item.stuffs.get(str(stuff_id), 0) >= amount

    def equip_add(self, oid, level=1, notify=True):
        # TODO 背包是否满了
        try:
            this_equip = ModelEquipment.all()[oid]
        except KeyError:
            raise InvalidOperate("Equipment Add: Char {0} Try to add a NONE exists Equipment oid: {1}".format(
                self.char_id, oid
            ))

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
            self._msg_equip(msg_equip, new_id, me, Equipment(self.char_id, new_id, self.item))
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
        if not self.has_equip(_id):
            raise InvalidOperate("Equipment Level Up: Char {0} Try to Level up a NONE exist equipment: {1}".format(
                self.char_id, _id
            ))

        e = Equipment(self.char_id, _id, self.item)
        e.level_up()


    def equip_step_up(self, _id, to):
        # TODO check stuffs
        if not self.has_equip(_id):
            raise InvalidOperate("Equipment Step Up: Char {0} Try to Step up a NONE exist equipmet: {1}".format(
                self.char_id, _id
            ))

        e = Equipment(self.char_id, _id, self.item)
        e.step_up(to)


    def equip_sell(self, _id):
        # TODO 装备在阵法插槽上
        if not self.has_equip(_id):
            raise InvalidOperate("Equipment Sell: Char {0} Try to sell a NONE exist equipment: {1}".format(
                self.char_id, _id
            ))

        e = Equipment(self.char_id, _id, self.item)
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

        e = Equipment(self.char_id, _id, self.item)
        if gem_id:
            off_gem = e.add_gem(slot_index, gem_id)
            self.gem_remove(gem_id, 1)
            if off_gem:
                self.gem_add([(off_gem, 1)])
        else:
            off_gem = e.rem_gem(slot_index)
            self.gem_add([(off_gem, 1)])

        self.item.save()


    def gem_add(self, add_gems):
        """

        @param add_gems: [(id, amount), (id, amount)]
        @type add_gems: list | tuple
        """

        all_gems = MysqlGem.all()

        for gid, _ in add_gems:
            if gid not in all_gems:
                raise InvalidOperate("Gem Add: Char {0} Try to add a NONE exist Gem, oid: {1}".format(
                    self.char_id, gid
                ))

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
        try:
            this_gem_amount = self.item.gems[str(_id)]
        except KeyError:
            raise InvalidOperate("Gem Merge: Char {0} Try to Merge a NONE exist gem: {1}".format(
                self.char_id, _id
            ))

        if this_gem_amount < 4:
            raise GemNotEnough("Gem Merge: Char {0} Try to Merge gem: {1}, But amount not enough. {2}".format(
                self.char_id, _id, this_gem_amount
            ))

        to_id = MysqlGem.all()[_id].merge_to
        if not to_id:
            raise InvalidOperate("Gem Merge: Char {0} Try to Merge gem: {1}. Which can not merge".format(
                self.char_id, _id
            ))

        self.gem_add([(to_id, 1)])
        self.gem_remove(_id, 4)


    def send_equip_notify(self):
        msg = protomsg.EquipNotify()
        for _id, data in self.item.equipments.iteritems():
            equip = msg.equips.add()
            self._msg_equip(equip, int(_id), data, Equipment(self.char_id, int(_id), self.item))

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