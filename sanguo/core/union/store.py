# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-12-10'


from core.exception import SanguoException
from core.union.base import UnionLoadBase, union_instance_check
from core.union.union import UnionBase
from core.union.member import Member
from core.resource import Resource

from core.signals import global_buff_changed_signal
from core.msgpipe import publish_to_char

from utils import pack_msg


from preset.data import UNION_STORE, STUFFS, HORSE, UNION_LEVEL
from preset import errormsg

import protomsg


BUFFS = [11,12,13]
BUFF_NAME_TABLE = {
    11: 'attack',
    12: 'defense',
    13: 'hp',
}
UNION_STORE_BUFF_STORE_ID_DICT = {}
for _k, _v in UNION_STORE.items():
    if _v.tp in BUFFS:
        UNION_STORE_BUFF_STORE_ID_DICT[_v.tp] = _k



class UnionStore(UnionLoadBase):
    def __init__(self, char_id):
        super(UnionStore, self).__init__(char_id)
        self.member = Member(char_id)

    def get_add_buffs_with_resource_id(self):
        cur_buy_times = self.buff_cur_buy_times

        def _get_value(buff_id):
            store_id = UNION_STORE_BUFF_STORE_ID_DICT[buff_id]
            value = UNION_STORE[store_id].value * cur_buy_times[buff_id]
            return value

        return {k: _get_value(k) for k in BUFFS}

    def get_add_buffs_with_string_name(self):
        buffs = self.get_add_buffs_with_resource_id()
        return {BUFF_NAME_TABLE[k]: v for k, v in buffs.items()}


    @property
    def buff_max_buy_times(self):
        return UNION_LEVEL[self.union.mongo_union.level].buff_max_buy_times


    @property
    def buff_cur_buy_times(self):
        cur_times = {}
        for i in BUFFS:
            cur_times[i] = self.member.mongo_union_member.buy_buff_times.get(str(i), 0)

        return cur_times

    @property
    def buff_cur_buy_cost(self):
        times = self.buff_cur_buy_times
        costs = {}
        for i in BUFFS:
            costs[i] = 20 + (times[i]+1) * 20

        return costs

    @union_instance_check(UnionBase, errormsg.UNION_NOT_EXIST, "UnionStore Buy", "has no union")
    def buy(self, _id, amount):
        try:
            item = UNION_STORE[_id]
        except KeyError:
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                "UnionStore Buy",
                "item {0} not exist".format(_id)
            )

        if item.tp in BUFFS:
            cost_coin = self.buff_cur_buy_cost[item.tp]
        else:
            cost_coin = item.union_coin

        self.member.check_coin(cost_coin, raise_exception=True, func_name="UnionStore Buy")

        if item.tp in BUFFS:
            self._buy_buff(_id, item.tp, amount)
        elif item.tp == 10:
            self._buy_horse(_id, item.value, amount)
        else:
            self._buy_items(_id, item.value, amount)

        self.member.cost_coin(cost_coin)


    def _buy_buff(self, _id, item_id, amount):
        cur_buy_times = self.buff_cur_buy_times
        max_buy_times = self.buff_max_buy_times
        if cur_buy_times[item_id] + amount > max_buy_times:
            raise SanguoException(
                errormsg.UNION_STORE_BUY_REACH_MAX_TIMES,
                self.char_id,
                "UnionStore Buy",
                "buff {0} has reached the max buy times {1}".format(item_id, max_buy_times)
            )

        self.member.mongo_union_member.buy_buff_times[str(item_id)] = cur_buy_times[item_id] + amount
        self.member.mongo_union_member.save()

        self.send_notify()

        global_buff_changed_signal.send(
            sender=None,
            char_id=self.char_id
        )



    def _buy_horse(self, _id, item_id, amount):
        if item_id not in HORSE:
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                self.char_id,
                "UnionStore Buy",
                "horse {0} not exist".format(item_id)
            )

        resources = Resource(self.char_id, "UnionStore Buy")
        resources.add(horses=[(item_id, amount)])

    def _buy_items(self, _id, item_id, amount):
        if item_id not in STUFFS:
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                self.char_id,
                "UnionStore Buy",
                "stuff {0} not exist".format(item_id)
            )

        resources = Resource(self.char_id, "UnionStore Buy")
        resources.add(stuffs=[(item_id, amount)])

    @union_instance_check(UnionBase, None, "UnionStore Send Notify")
    def send_notify(self):
        msg = protomsg.UnionStoreNotify()
        max_times = self.buff_max_buy_times
        cur_times = self.buff_cur_buy_times
        buy_cost = self.buff_cur_buy_cost

        add_buffs = self.get_add_buffs_with_resource_id()

        for i in BUFFS:
            msg_buff = msg.buffs.add()
            msg_buff.id = i
            msg_buff.max_times = max_times
            msg_buff.cur_times = cur_times[i]
            msg_buff.add_value = add_buffs[i]
            msg_buff.cost = buy_cost[i]

        publish_to_char(self.char_id, pack_msg(msg))

