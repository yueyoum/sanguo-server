# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/14/14'

import random

from mongoengine import DoesNotExist
from core.mongoscheme import MongoItem, MongoEmbeddedEquipment
from core.exception import SanguoException
from core.msgpipe import publish_to_char
from core.character import Char
from core.signals import equip_changed_signal
from core.formation import Formation
from core.achievement import Achievement
from core.task import Task
from core.resource import Resource
from utils import pack_msg
from utils.functional import id_generator
import protomsg
from preset.settings import EQUIP_MAX_LEVEL, EQUIP_SELL_QUALITY_BASE
from preset.data import EQUIPMENTS, GEMS, STUFFS
from preset import errormsg
from dll import external_calculate


def equip_updated(func):
    def deco(self, *args, **kwargs):
        res = func(self, *args, **kwargs)
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



    @equip_updated
    def level_up(self, quick=False):
        def _up():
            if self.level >= EQUIP_MAX_LEVEL:
                raise SanguoException(
                    errormsg.EQUIPMENT_REACH_MAX_LEVEL,
                    self.char_id,
                    "Equipment Level Up",
                    "Equipment {0} has already touch max level {1}".format(self.equip.id, EQUIP_MAX_LEVEL))

            if self.level >= char_level:
                raise SanguoException(
                    errormsg.EQUIPMENT_REACH_CHAR_LEVEL,
                    self.char_id,
                    "Equipment Level Up",
                    "Equipment {0} level {1} >= char level {2}".format(self.equip.id, self.level, char_level)
                )

            gold_needs = self.level_up_need_gold()
            if cache_char.gold < gold_needs:
                raise SanguoException(
                    errormsg.GOLD_NOT_ENOUGH,
                    self.char_id,
                    "Equipment Level Up",
                    "Gold Not Enough"
                )

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
        cache_char = char.mc
        char_level = cache_char.level
        LEVEL_UP_PROBS = (
            (30, 1), (80, 2), (100, 3)
        )

        all_gold_needs = 0
        equip_msgs = []


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

        resource = Resource(self.char_id, "Equipment Level Up", "equipment {0}".format(self.equip_id))
        with resource.check(gold=-all_gold_needs):
            self.mongo_item.save()

        Task(self.char_id).trig(8)
        return equip_msgs



    @equip_updated
    def step_up(self):
        to = self.equip.upgrade_to
        if not to:
            raise SanguoException(
                errormsg.EQUIPMENT_REACH_MAX_STEP,
                self.char_id,
                "Equipment Step Up",
                "Equipment {0} Can not step up".format(self.equip_id)
            )

        step_up_need_gold = self.step_up_need_gold()

        stuff_needs = []
        for x in self.equip.stuff_needs.split(','):
            _id, _amount = x.split(':')
            stuff_needs.append((int(_id), int(_amount)))

        resouce = Resource(self.char_id, "Equipment Step Up", "equipment {0}".format(self.equip_id))
        with resouce.check(gold=-step_up_need_gold, stuffs=stuff_needs):
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
            raise SanguoException(
                errormsg.EQUIPMENT_ADD_GEM_IN_NONE_SLOT,
                self.char_id,
                "Equipment Add Gem",
                "Equipment {0} gems IndexError. index {1}".format(self.equip_id, index)
            )

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
            raise SanguoException(
                errormsg.EQUIPMENT_REM_GEM_IN_NONE_SLOT,
                self.char_id,
                "Equipment Rem Gem",
                "Equipment {0} gems IndexError. index {1}".format(self.equip_id, index)
            )

        self.mongo_item.save()
        return off_gem


    def sell_gold(self):
        # 出售价格 金币
        step = EQUIPMENTS[self.oid].step
        base = EQUIP_SELL_QUALITY_BASE[step]
        total_gold = 100 * (1 - pow(1.08, self.level)) / (1 - 1.08)
        total = total_gold + base
        return int(total)

    def level_up_need_gold(self):
        # 强化升级所需金币
        gold = pow(1.09, (self.level - 1)) * 200 + 100
        return int(gold)


    def step_up_need_gold(self):
        return int(round(1000 * pow(1.7, self.equip.step), -3))


    @property
    def attack(self):
        if not self.equip.attack:
            return 0

        return external_calculate.Equipment.attack(self.equip.attack, self.level, self.equip.growing)

    @property
    def defense(self):
        if not self.equip.defense:
            return 0

        return external_calculate.Equipment.defense(self.equip.defense, self.level, self.equip.growing)

    @property
    def hp(self):
        if not self.equip.hp:
            return 0

        return external_calculate.Equipment.hp(self.equip.hp, self.level, self.equip.growing)


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
            crit = (1 - pow(0.99, attrs['crit'] / 10.0)) * 100
            attrs['crit'] = round(crit, 2)

        return attrs

    def get_embedded_gems(self):
        return self.mongo_item.equipments[str(self.equip_id)].gems

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
        try:
            this_equip = EQUIPMENTS[oid]
        except KeyError:
            raise SanguoException(
                errormsg.EQUIPMENT_NOT_EXIST,
                self.char_id,
                "Equipment Add",
                "Equipment {0} NOT exist".format(oid)
            )

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
                raise SanguoException(
                    errormsg.EQUIPMENT_NOT_EXIST,
                    self.char_id,
                    "Equipment Remove",
                    "Equipment {0} NOT exist".format(_id)
                )

        for _id in ids:
            self.item.equipments.pop(str(_id))

        self.item.save()

        msg = protomsg.RemoveEquipNotify()
        msg.ids.extend(ids)
        publish_to_char(self.char_id, pack_msg(msg))


    def equip_level_up(self, _id, quick):
        if not self.has_equip(_id):
            raise SanguoException(
                errormsg.EQUIPMENT_NOT_EXIST,
                self.char_id,
                "Equipment Level Up",
                "Equipment {0} NOT exist".format(_id)
            )

        e = Equipment(self.char_id, _id, self.item)
        return e.level_up(quick=quick)


    def equip_step_up(self, equip_id):
        if not self.has_equip(equip_id):
            raise SanguoException(
                errormsg.EQUIPMENT_NOT_EXIST,
                self.char_id,
                "Equipment Step Up",
                "Equipment {0} NOT exist".format(equip_id)
            )

        equip = Equipment(self.char_id, equip_id, self.item)
        equip.step_up()


    def equip_check_sell(self, ids):
        if not isinstance(ids, (set, list, tuple)):
            ids = [ids]

        f = Formation(self.char_id)
        ids = set(ids)
        for _id in ids:
            if not self.has_equip(_id):
                raise SanguoException(
                    errormsg.EQUIPMENT_NOT_EXIST,
                    self.char_id,
                    "Equipment Check Sell",
                    "Equipment {0} NOT exist".format(_id)
                )

            if f.find_socket_by_equip(_id):
                raise SanguoException(
                    errormsg.EQUIPMENT_CANNOT_SELL_FORMATION,
                    self.char_id,
                    "Equipment Check Sell",
                    "Equipment {0} in Formation, Can not sell".format(_id)
                )


    def equip_sell(self, ids):
        if not isinstance(ids, (set, list, tuple)):
            ids = [ids]

        self.equip_check_sell(ids)

        off_gems = {}

        gold = 0
        for _id in ids:
            e = Equipment(self.char_id, _id, self.item)
            gold += e.sell_gold()
            for gid in e.get_embedded_gems():
                if gid:
                    off_gems[gid] = off_gems.get(gid, 0) + 1

        resource = Resource(self.char_id, "Equipment Sell", "equipments {0}".format(ids))
        resource.check_and_remove(equipments=list(ids))
        resource.add(gold=gold)

        self.gem_add(off_gems.items())


    def equip_embed(self, _id, slot_id, gem_id):
        # gem_id = 0 表示取下slot_id对应的宝石
        if not self.has_equip(_id):
            raise SanguoException(
                errormsg.EQUIPMENT_NOT_EXIST,
                self.char_id,
                "Equipment Embed Gem",
                "Equipment {0} NOT exist".format(_id)
            )

        if gem_id and not self.has_gem(gem_id):
            raise SanguoException(
                errormsg.GEM_NOT_EXIST,
                self.char_id,
                "Equipment Embed Gem",
                "Gem {0} NOT exist".format(gem_id)
            )


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


    def gem_add(self, add_gems, send_notify=True):
        """

        @param add_gems: [(id, amount), (id, amount)]
        @type add_gems: list | tuple
        """

        for gid, _ in add_gems:
            if gid not in GEMS:
                raise SanguoException(
                    errormsg.GEM_NOT_EXIST,
                    self.char_id,
                    "Gem Add",
                    "Gem {0} not exist".format(gid)
                )


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
            raise SanguoException(
                errormsg.GEM_NOT_EXIST,
                self.char_id,
                "Gem Remove",
                "Gem {0} not exist".format(_id)
            )

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


    def gem_check_sell(self, _id, _amount):
        if not self.has_gem(_id, _amount):
            raise SanguoException(
                errormsg.GEM_NOT_EXIST,
                self.char_id,
                "Gem Check Sell",
                "Gem {0}, amount {1} not exist/enough".format(_id, _amount)
            )

    def gem_sell(self, _id, amount):
        try:
            this_gem = GEMS[_id]
        except KeyError:
            raise SanguoException(
                errormsg.GEM_NOT_EXIST,
                self.char_id,
                "Gem Sell",
                "Gem {0} not exist".format(_id)
            )

        gold = this_gem.sell_gold * amount

        resource = Resource(self.char_id, "Gem Sell", "sell: {0}, amount {1}".format(_id, amount))
        resource.check_and_remove(gems=[(_id, amount)])
        resource.add(gold=gold)


    def gem_merge(self, _id):
        this_gem_amount = self.item.gems.get(str(_id), 0)
        if this_gem_amount == 0:
            raise SanguoException(
                errormsg.GEM_NOT_EXIST,
                self.char_id,
                "Gem Merge",
                "Gem {0} not exist".format(_id)
            )

        elif this_gem_amount < 4:
            raise SanguoException(
                errormsg.GEM_NOT_ENOUGH,
                self.char_id,
                "Gem Merge",
                "Gem {0} not enough. {1} < 4".format(_id, this_gem_amount)
            )

        to_id = GEMS[_id].merge_to
        if not to_id:
            raise SanguoException(
                errormsg.GEM_CAN_NOT_MERGE,
                self.char_id,
                "Gem Merge",
                "Gem {0} can not merge".format(_id)
            )

        self.gem_remove(_id, 4)
        self.gem_add([(to_id, 1)])

        to_gem_obj = GEMS[to_id]

        achievement = Achievement(self.char_id)
        achievement.trig(25, 1)
        achievement.trig(26, to_gem_obj.level)

        return to_id


    def stuff_add(self, add_stuffs, send_notify=True):
        """

        @param add_stuffs: [(id, amount), (id, amount)]
        @type add_stuffs: list | tuple
        """
        for _id, _ in add_stuffs:
            if _id not in STUFFS:
                raise SanguoException(
                    errormsg.STUFF_NOT_EXIST,
                    self.char_id,
                    "Stuff Add",
                    "Stuff Oid {0} not exist".format(_id)
                )

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
            raise SanguoException(
                errormsg.STUFF_NOT_EXIST,
                self.char_id,
                "Stuff Remove",
                "Stuff {0} not exist".format(_id)
            )

        new_amount = this_stuff_amount - amount

        if new_amount < 0:
            raise SanguoException(
                errormsg.STUFF_NOT_ENOUGH,
                self.char_id,
                "Stuff Remove",
                "Stuff {0} not enough".format(_id)
            )

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

    def stuff_check_sell(self, _id, amount):
        if not self.has_stuff(_id, amount):
            raise SanguoException(
                errormsg.STUFF_NOT_EXIST,
                self.char_id,
                "Stuff Check Sell",
                "Stuff {0}, amount {1} not exist/enough".format(_id, amount)
            )


    def stuff_sell(self, _id, amount):
        try:
            this_stuff = STUFFS[_id]
        except KeyError:
            raise SanguoException(
                errormsg.STUFF_NOT_EXIST,
                self.char_id,
                "Stuff Sell",
                "Stuff {0} not exist".format(_id)
            )

        gold = this_stuff.sell_gold * amount

        resource = Resource(self.char_id, "Stuff Sell", "sell {0}, amount: {1}".format(_id, amount))
        resource.check_and_remove(stuffs=[(_id, amount)])
        resource.add(gold=gold)


    @classmethod
    def get_sutff_drop(cls, _id):
        # 获得宝箱中的 drop
        from core.attachment import get_drop, is_empty_drop

        s = STUFFS[_id]
        packages = s.packages
        if not packages:
            return None

        package_ids = [int(i) for i in packages.split(',')]
        prepare_drop = get_drop(package_ids)
        if is_empty_drop(prepare_drop) and s.default_package:
            package_ids = [s.default_package]
            prepare_drop = get_drop(package_ids)

        return prepare_drop


    def stuff_use(self, _id, amount):
        from core.attachment import get_drop, standard_drop_to_attachment_protomsg, is_empty_drop
        from core.resource import Resource
        try:
            s = STUFFS[_id]
        except KeyError:
            raise SanguoException(
                errormsg.STUFF_NOT_EXIST,
                self.char_id,
                "Stuff Use",
                "stuff {0} not exist".format(_id)
            )

        # XXX
        if s.tp != 3:
            raise SanguoException(
                errormsg.STUFF_CAN_NOT_USE,
                self.char_id,
                "Stuff Use",
                "stuff {0} tp is {1}. Can not use".format(_id, s.tp)
            )

        # XXX 忽略amount，只能一个一个用
        self.stuff_remove(_id, amount)

        prepare_drop = self.get_sutff_drop(_id)
        if not prepare_drop:
            return None

        resource = Resource(self.char_id, "Stuff Use", "use {0}".format(_id))
        standard_drop = resource.add(**prepare_drop)
        return standard_drop_to_attachment_protomsg(standard_drop)



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
