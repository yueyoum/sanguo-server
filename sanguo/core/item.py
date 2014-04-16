# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/14/14'

import random

from django.db import transaction

from mongoengine import DoesNotExist

from core.mongoscheme import MongoItem, MongoEmbeddedEquipment

from core.exception import InvalidOperate, GoldNotEnough, GemNotEnough, StuffNotEnough, SanguoException
from core.msgpipe import publish_to_char
from core.character import Char
from core.signals import equip_changed_signal
from core.formation import Formation
from core.achievement import Achievement
from core.task import Task

from core import DLL

from utils import pack_msg
from utils import cache
from utils.functional import id_generator

import protomsg

from preset.settings import EQUIP_MAX_LEVEL
from preset.data import EQUIPMENTS, GEMS, STUFFS



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
        msg.step_up_need_gold = equip_obj.step_up_need_gold()
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

        self.equip = EQUIPMENTS[self.oid]

    # @staticmethod
    # def cache_obj(equip_id):
    #     e = cache.get('equip:{0}'.format(equip_id))
    #     if e:
    #         return e

    @equip_updated
    def level_up(self, quick=False):
        def _up():
            if self.level >= EQUIP_MAX_LEVEL:
                raise InvalidOperate("Equipment Level Up. Char {0} Try Level Up Equipment {1}. But Equipment already level {2}".format(
                    self.char_id, self.equip_id, self.level
                ))

            if self.level >= char_level:
                raise SanguoException(501, "Equipment Level Up. Char {0} Try level up equipment {1}. But equipment level {2} can't great than char's level {3}".format(
                    self.char_id, self.equip_id, self.level, char_level
                ))

            gold_needs = self.level_up_need_gold()
            if cache_char.gold < gold_needs:
                raise GoldNotEnough("Equipment Level Up. Char {0} Gold {1} Not Enough. Needs {2}".format(
                    self.char_id, cache_char.gold, gold_needs
                ))

            # char.update(gold=-gold_needs)
            cache_char.gold -= gold_needs

            prob = random.randint(1, 100)
            for p, l in LEVEL_UP_PROBS:
                if prob <= p:
                    actual_level_up = l
                    break

            self.mongo_item.equipments[str(self.equip_id)].level += actual_level_up
            self.level += actual_level_up
            return gold_needs


        char = Char(self.char_id)
        cache_char = char.cacheobj
        char_level = cache_char.level
        LEVEL_UP_PROBS = (
            (30, 1), (80, 2), (100, 3)
        )

        all_gold_needs = 0

        equip_msgs = []

        old_level = self.mongo_item.equipments[str(self.equip_id)].level

        if quick:
            quick_times = 0
            while True:
                try:
                    all_gold_needs += _up()
                except SanguoException:
                    if quick_times == 0:
                        raise
                    else:
                        break
                else:
                    quick_times += 1
                    msg = protomsg.Equip()
                    self._msg_equip(msg, self.equip_id, self.mongo_item.equipments[str(self.equip_id)], self)
                    equip_msgs.append(msg)
        else:
            all_gold_needs += _up()
            msg = protomsg.Equip()
            self._msg_equip(msg, self.equip_id, self.mongo_item.equipments[str(self.equip_id)], self)
            equip_msgs.append(msg)

        new_level = self.mongo_item.equipments[str(self.equip_id)].level

        char.update(gold=-all_gold_needs, des='Equipment Level up. {1} from {0} to {1}'.format(self.equip_id, old_level, new_level))
        self.mongo_item.save()

        return equip_msgs



    @equip_updated
    def step_up(self):
        to = self.equip.upgrade_to
        if not to:
            raise InvalidOperate("Equipment Step Up: char {0} Try to Step up equipment {1}. But Can't step up".format(
                self.char_id, self.equip_id
            ))

        stuff_needs = []
        for x in self.equip.stuff_needs.split(','):
            _id, _amount = x.split(':')
            stuff_needs.append((int(_id), int(_amount)))

        for _id, _amount in stuff_needs:
            if self.mongo_item.stuffs.get(str(_id), 0) < _amount:
                raise StuffNotEnough("Equipment Step Up: Char {0} Try to step up equipment {1}. But Stuff {2} NOT enough".format(
                    self.char_id, self.equip_id, _id
                ))

        # 在外面使用Item类的 stuff_remove 方法

        char = Char(self.char_id)
        cache_char = char.cacheobj
        step_up_need_gold = self.step_up_need_gold()
        if cache_char.gold < step_up_need_gold:
            raise GoldNotEnough("Equipment Step Up: Char {0} Try to step up equipent {1}. But Gold NOT enough".format(
                self.char_id, self.equip_id
            ))

        char.update(gold=-step_up_need_gold, des='Equipment Step up. {0} step up from {1} to {2}'.format(
            self.equip_id, self.mongo_item.equipments[str(self.equip_id)].oid, to
        ))

        self.oid = to
        self.equip = EQUIPMENTS[self.oid]

        self.mongo_item.equipments[str(self.equip_id)].oid = to
        add_gem_slots = self.equip.slots - len(self.mongo_item.equipments[str(self.equip_id)].gems)
        for i in range(add_gem_slots):
            self.mongo_item.equipments[str(self.equip_id)].gems.append(0)

        self.mongo_item.save()

        achievement = Achievement(self.char_id)
        achievement.trig(22, 1)
        if not self.equip.upgrade_to:
            achievement.trig(23, 1)

        return stuff_needs


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

        gem_amount = 0
        for g in self.mongo_item.equipments[str(self.equip_id)].gems:
            if g != 0:
                gem_amount += 1

        achievement = Achievement(self.char_id)
        achievement.trig(24, gem_amount)

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
        # gold = pow(1.08, self.level) * 100
        gold = 1.08 * (self.level - 1) * 200
        return int(gold)


    def step_up_need_gold(self):
        return int(round(1000 * pow(1.7, self.equip.step), -3))


    @property
    def attack(self):
        if not self.equip.attack:
            return 0

        # return self.equip.attack + self.level * self.equip.growing
        return DLL.equip_attack(self.equip.attack, self.level, self.equip.growing)

    @property
    def defense(self):
        if not self.equip.defense:
            return 0

        # return self.equip.defense + self.level * self.equip.growing
        return DLL.equip_defense(self.equip.defense, self.level, self.equip.growing)

    @property
    def hp(self):
        if not self.equip.hp:
            return 0

        # return self.equip.hp + self.level * self.equip.growing
        return DLL.equip_hp(self.equip.hp, self.level, self.equip.growing)


    @property
    def gem_attributes(self):
        attrs = {}

        gems = self.mongo_item.equipments[str(self.equip_id)].gems
        for gid in gems:
            if not gid:
                continue
            gem = GEMS[gid]
            attrs[gem.used_for] = attrs.get(gem.used_for, 0) + gem.value

        for k, v in attrs.iteritems():
            attrs[k] *= (1 + self.equip.gem_addition / 100.0)

        # hp为整数
        if 'hp' in attrs:
            attrs['hp'] = int(attrs['hp'])

        # 暴击修正
        if 'crit' in attrs:
            attrs['crit'] = int((1 - pow(0.99, attrs['crit'] / 10.0)) * 100)

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
            this_equip = EQUIPMENTS[oid]
        except KeyError:
            raise InvalidOperate("Equipment Add: Char {0} Try to add a NONE exists Equipment oid: {1}".format(
                self.char_id, oid
            ))

        # new_id = document_ids.inc('equipment')
        new_id = id_generator('equipment')[0]
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

    def equip_remove(self, ids):
        if not isinstance(ids, (set, list, tuple)):
            ids = [ids]

        ids = set(ids)
        for _id in ids:
            if not self.has_equip(_id):
                raise InvalidOperate("Equipment Remove: Char {0} Try to Remove a NONE exist equipment: {1}".format(
                    self.char_id, _id
                ))

        for _id in ids:
            self.item.equipments.pop(str(_id))

        self.item.save()

        msg = protomsg.RemoveEquipNotify()
        msg.ids.extend(ids)
        publish_to_char(self.char_id, pack_msg(msg))


    def equip_level_up(self, _id, quick):
        if not self.has_equip(_id):
            raise InvalidOperate("Equipment Level Up: Char {0} Try to Level up a NONE exist equipment: {1}".format(
                self.char_id, _id
            ))

        e = Equipment(self.char_id, _id, self.item)
        return e.level_up(quick=quick)


    def equip_step_up(self, equip_id):
        if not self.has_equip(equip_id):
            raise InvalidOperate("Equipment Step Up: Char {0} Try to Step up a NONE exist equipmet: {1}".format(
                self.char_id, equip_id
            ))

        equip = Equipment(self.char_id, equip_id, self.item)
        stuff_needs = equip.step_up()
        for _id, _amount in stuff_needs:
            self.stuff_remove(_id, _amount)


    def equip_sell(self, ids):
        if not isinstance(ids, (set, list, tuple)):
            ids = [ids]

        f = Formation(self.char_id)
        ids = set(ids)
        for _id in ids:
            if not self.has_equip(_id):
                raise InvalidOperate("Equipment Sell: Char {0} Try to sell a NONE exist equipment: {1}".format(
                    self.char_id, _id
                ))

            if f.find_socket_by_equip(_id):
                raise InvalidOperate("Eequipment Sell: Char {0} Try to sell equipment {1}. But it in formation socket".format(
                    self.char_id, _id
                ))

        gold = 0
        for _id in ids:
            e = Equipment(self.char_id, _id, self.item)
            gold += e.sell_gold()

        char = Char(self.char_id)
        char.update(gold=gold, des='Equipment Sell. sell {0}'.format(ids))
        self.equip_remove(ids)

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


    def special_buy(self, socket_id, tp):
        f = Formation(self.char_id)
        f.special_buy(socket_id, tp)


    def gem_add(self, add_gems, send_notify=True):
        """

        @param add_gems: [(id, amount), (id, amount)]
        @type add_gems: list | tuple
        """

        for gid, _ in add_gems:
            if gid not in GEMS:
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

        if not send_notify:
            return
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


    def gem_sell(self, _id, amount):
        # TODO get gold
        gold = 10 * amount
        self.gem_remove(_id, amount)

        char = Char(self.char_id)
        char.update(gold=gold, des="Gem Sell")

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

        to_id = GEMS[_id].merge_to
        if not to_id:
            raise InvalidOperate("Gem Merge: Char {0} Try to Merge gem: {1}. Which can not merge".format(
                self.char_id, _id
            ))

        self.gem_add([(to_id, 1)])
        self.gem_remove(_id, 4)

        to_gem_obj = GEMS[to_id]

        achievement = Achievement(self.char_id)
        achievement.trig(25, 1)
        achievement.trig(26, to_gem_obj.level)

        t = Task(self.char_id)
        t.trig(4)


    def stuff_add(self, add_stuffs, send_notify=True):
        """

        @param add_stuffs: [(id, amount), (id, amount)]
        @type add_stuffs: list | tuple
        """
        for _id, _ in add_stuffs:
            if _id not in STUFFS:
                raise InvalidOperate("Stuff Add: Char {0} Try to add a NONE exist Stuff: {1}".format(
                    self.char_id, _id
                ))

        stuffs = self.item.stuffs
        add_stuffs_dict = {}
        for _id, _amount in add_stuffs:
            add_stuffs_dict[_id] = add_stuffs_dict.get(_id, 0) + _amount

        new_stuffs = []
        update_stuffs = []
        for _id, _amount in add_stuffs_dict.iteritems():
            sid = str(_id)
            if sid in stuffs:
                stuffs[sid] += _amount
                update_stuffs.append((_id, stuffs[sid]))
            else:
                stuffs[sid] = _amount
                new_stuffs.append((_id, _amount))

        self.item.stuffs = stuffs
        self.item.save()

        if not send_notify:
            return
        if new_stuffs:
            msg = protomsg.AddStuffNotify()
            for k, v in new_stuffs:
                s = msg.stuffs.add()
                s.id, s.amount = k, v

            publish_to_char(self.char_id, pack_msg(msg))

        if update_stuffs:
            msg = protomsg.UpdateStuffNotify()
            for k, v in update_stuffs:
                s = msg.stuffs.add()
                s.id, s.amount = k, v

            publish_to_char(self.char_id, pack_msg(msg))



    def stuff_remove(self, _id, amount):
        """
        @param _id: stuff id
        @type _id: int
        @param amount: this stuff amount
        @type amount: int
        """
        try:
            this_stuff_amount = self.item.stuffs[str(_id)]
        except KeyError:
            raise InvalidOperate("Stuff Remove: Char {0} Try to remove a NONE exist stuff: {1}".format(self.char_id, _id))

        new_amount = this_stuff_amount - amount

        if new_amount < 0:
            raise StuffNotEnough("Stuff Remove: Char {0} Try to remove {1}. But not enough, {2} < {3}".format(
                self.char_id, _id, this_stuff_amount, amount
            ))

        if new_amount == 0:
            self.item.stuffs.pop(str(_id))
            self.item.save()

            msg = protomsg.RemoveStuffNotify()
            msg.ids.append(_id)
            publish_to_char(self.char_id, pack_msg(msg))
        else:
            self.item.stuffs[str(_id)] = new_amount
            self.item.save()
            msg = protomsg.UpdateStuffNotify()
            g = msg.stuffs.add()
            g.id, g.amount = _id, new_amount

            publish_to_char(self.char_id, pack_msg(msg))


    def stuff_sell(self, _id, amount):
        # TODO get gold
        gold = 10 * amount
        self.stuff_remove(_id, amount)

        char = Char(self.char_id)
        char.update(gold=gold, des="Gem Sell")



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

    def send_stuff_notify(self):
        msg = protomsg.StuffNotify()
        for k, v in self.item.stuffs.iteritems():
            s = msg.stuffs.add()
            s.id, s.amount = int(k), v

        publish_to_char(self.char_id, pack_msg(msg))


    def send_notify(self):
        self.send_equip_notify()
        self.send_gem_notify()
        self.send_stuff_notify()