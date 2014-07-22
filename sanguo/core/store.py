# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/20/14'

from mongoengine import DoesNotExist

from core.mongoscheme import MongoStoreCharLimit
from core.msgpipe import publish_to_char
from core.character import Char
from core.exception import SanguoException
from core.resource import Resource

from utils import pack_msg
from utils.api import api_store_buy, api_store_get, APIFailure

from protomsg import StoreNotify
from preset import errormsg



class Store(object):
    def __init__(self, char_id):
        self.char_id = char_id

        try:
            self.mc_limit = MongoStoreCharLimit.objects.get(id=self.char_id)
        except DoesNotExist:
            self.mc_limit = MongoStoreCharLimit(id=self.char_id)
            self.mc_limit.limits = {}
            self.mc_limit.save()

    def get_new_store(self):
        try:
            data = api_store_get({})
        except APIFailure:
            raise SanguoException(
                errormsg.SERVER_FAULT,
                self.char_id,
                "Store",
                "APIFailure. api_store_get"
            )

        store = data['data']['store']
        return {int(k): v for k, v in store.iteritems()}


    def buy(self, _id, amount):
        if amount < 1:
            raise SanguoException(
                errormsg.STORE_INVALID_BUY_AMOUNT,
                self.char_id,
                "Store Buy",
                "invalid amount {0}".format(amount)
            )

        store = self.get_new_store()

        try:
            this_goods = store[_id]
        except KeyError:
            raise SanguoException(
                errormsg.STORE_GOODS_NOT_EXIST,
                self.char_id,
                "Store Buy",
                "{0} not exist".format(_id)
            )

        char = Char(self.char_id)
        mc = char.mc

        # check vip
        if this_goods['vip_condition'] > mc.vip:
            raise SanguoException(
                errormsg.STORE_GOODS_VIP_CONDITION,
                self.char_id,
                "Store Buy",
                "{0} has vip condition {1}. greater than char vip {2}".format(_id, this_goods['vip_condition'], mc.vip)
            )

        # check level
        if this_goods['level_condition'] > mc.level:
            raise SanguoException(
                errormsg.STORE_GOODS_LEVEL_CONDITION,
                self.char_id,
                "Store Buy",
                "{0} has level condition {1}. greater than char level {2}".format(_id, this_goods['level_condition'], mc.level)
            )

        # check total amount
        if this_goods['has_total_amount']:
            if this_goods['total_amount_run_time'] < amount:
                raise SanguoException(
                    errormsg.STORE_GOODS_AMOUNT_NOT_ENOUGH,
                    self.char_id,
                    "Store Buy",
                    "{0} amount not enough. remained {1}, buy amount {2}".format(_id, this_goods['total_amount_run_time'], amount)
                )

        # check limit
        if this_goods['has_limit_amount']:
            remained_amount = self.get_limit_remained_amount(_id, this_goods['limit_amount'])
            if remained_amount < amount:
                raise SanguoException(
                    errormsg.STORE_GOODS_CHAR_LIMIT,
                    self.char_id,
                    "Store Buy",
                    "{0} reach limit {1}".format(_id, this_goods['limit_amount'])
                )

        # check gold or sycee
        wealth_needs = this_goods['sell_price'] * amount

        if this_goods['sell_type'] == 1:
            resource_need = {'gold': -wealth_needs}
        else:
            resource_need = {'sycee': -wealth_needs}

        resource = Resource(self.char_id, "Store Buy", 'buy {0}, amount: {1}'.format(_id, amount))
        with resource.check(**resource_need):
            # 本地server检查完毕，然后通过API通知HUB购买。
            # 对于有total amount限制的物品，HUB可能返回错误
            data = {
                'char_id': self.char_id,
                'goods_id': _id,
                'goods_amount': amount,
            }

            try:
                res = api_store_buy(data)
            except APIFailure:
                raise SanguoException(
                    errormsg.SERVER_FAULT,
                    self.char_id,
                    "Store",
                    "APIFailure. api_store_buy"
                )

            if res['ret'] != 0:
                raise SanguoException(
                    res['ret'],
                    self.char_id,
                    "Store Buy",
                    "api failure"
                )

            # ALL OK
            # 开始操作
            if this_goods['has_limit_amount']:
                # 有每人限量的记录到每人的购买记录中
                self.mc_limit.limits[str(_id)] = self.mc_limit.limits.get(str(_id), 0) + amount
                self.mc_limit.save()

            # 更新store
            if this_goods['has_total_amount']:
                store[_id]['total_amount_run_time'] = res['data']['total_amount_run_time']

            # 给东西
            resource_add = {}
            if this_goods['item_tp'] == 1:
                resource_add['heros'] = [(this_goods['item_id'], amount)]
            elif this_goods['item_tp'] == 2:
                resource_add['equipments'] = [(this_goods['item_id'], 1, amount)]
            elif this_goods['item_tp'] == 3:
                resource_add['gems'] = [(this_goods['item_id'], amount)]
            else:
                resource_add['stuffs'] = [(this_goods['item_id'], amount)]

            resource.add(**resource_add)

        self.send_notify(store=store)



    def get_limit_already_amount(self, gid):
        return self.mc_limit.limits.get(str(gid), 0)

    def get_limit_remained_amount(self, gid, limit_amount):
        already_amount = self.get_limit_already_amount(gid)
        remained = limit_amount - already_amount
        if remained < 0:
            remained = 0
        return remained


    def fill_up_notify_msg(self, store=None):
        c = Char(self.char_id)
        mc = c.mc

        if not store:
            store = self.get_new_store()

        msg = StoreNotify()
        msg.session = ""

        for k, v in store.items():
            if v['level_condition'] > mc.level:
                store.pop(k)
                continue

            g = msg.goods.add()
            g.id = v['id']
            g.tag = v['tag']
            g.item_tp = v['item_tp']
            g.item_id = v['item_id']
            g.sell_tp = v['sell_type']
            g.original_price = v['original_price']
            g.sell_price = v['sell_price']

            if v['has_total_amount']:
                g.conditions.append(1)
                g.total_condition.amount = v['total_amount_run_time']

            if v['has_limit_amount']:
                g.conditions.append(2)
                g.limit_condition.amount = self.get_limit_remained_amount(v['id'], v['limit_amount'])

            if v['vip_condition'] > 0:
                g.conditions.append(3)
                g.vip_condition.vip = v['vip_condition']
                g.vip_condition.can_buy = mc.vip >= v['vip_condition']

        return msg


    def send_notify(self, store=None):
        msg = self.fill_up_notify_msg(store=store)
        publish_to_char(self.char_id, pack_msg(msg))
