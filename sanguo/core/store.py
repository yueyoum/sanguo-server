# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/20/14'

from mongoengine import DoesNotExist

from core.mongoscheme import MongoStoreCharLimit
from core.msgpipe import publish_to_char
from core.character import Char
from core.item import Item
from core.hero import save_hero
from core.exception import InvalidOperate, GoldNotEnough, SyceeNotEnough

from utils import pack_msg
from utils.api import api_store_buy, api_store_get


from protomsg import StoreNotify



class Store(object):
    def __init__(self, char_id):
        self.char_id = char_id

        try:
            self.mc_limit = MongoStoreCharLimit.objects.get(id=self.char_id)
        except DoesNotExist:
            self.mc_limit = MongoStoreCharLimit(id=self.char_id)

    def get_new_store(self):
        data = api_store_get({})
        store = data['data']['store']
        return store

    def buy(self, _id, amount):
        store = self.get_new_store()

        try:
            this_goods = store[_id]
        except KeyError:
            raise InvalidOperate("Store Buy. Char {0} Try to buy a NONE exists goods {1}".format(self.char_id, _id))

        char = Char(self.char_id)
        mc = char.mc

        # TODO check vip
        # if this_goods['vip_condition'] > mc.vip:
        #     raise InvalidOperate("Store Buy. Char {0} Try to buy {1}. But vip test not passed. {2} < {3}".format(
        #         self.char_id, _id, mc.vip, this_goods['vip_condition']
        #     ))

        # check level
        if this_goods['level_condition'] > mc.level:
            raise InvalidOperate("Store Buy. Char {0} Try to buy {1}. But level test not passed. {2} < {3}".format(
                self.char_id, _id, mc.level, this_goods['level_condition']
            ))

        # check total amount
        if this_goods['has_total_amount']:
            if this_goods['total_amount_run_time'] < amount:
                raise InvalidOperate("Store Buy. Char {0} Try to buy {1}. Buy total_amount_run_time {2} < amount {3}".format(
                    self.char_id, _id, this_goods['total_amount_run_time'], amount
                ))

        # check limit
        if this_goods['has_limit_amount']:
            remained_amount = self.get_limit_remained_amount(_id, this_goods['limit_amount'])
            if remained_amount < amount:
                raise InvalidOperate("Store Buy. Char {0} Try to buy {1}. Buy limit remained amount {2} < amount {3}".format(
                    self.char_id, _id, remained_amount, amount
                ))

        # check gold or sycee
        wealth_needs = this_goods['sell_price'] * amount

        if this_goods['sell_type'] == 1:
            if mc.gold < wealth_needs:
                raise GoldNotEnough("Store Buy. Char {0} try to buy {1}. But gold not enough. {2} < {3}".format(
                    self.char_id, _id, mc.gold, wealth_needs
                ))
        else:
            if mc.sycee < wealth_needs:
                raise SyceeNotEnough("Store Buy. Char {0} try to buy {1}. But sycee not enough. {2} < {3}".format(
                    self.char_id, _id, mc.sycee, wealth_needs
                ))


        # 本地server检查完毕，然后通过API通知HUB购买。
        # 对于有total amount限制的物品，HUB可能返回错误
        data = {
            'char_id': self.char_id,
            'goods_id': _id,
            'goods_amount': amount,
        }

        res = api_store_buy(data)
        if res['ret'] != 0:
            # FIXME error code
            raise InvalidOperate("Store Buy. Char {0} try to buy {1}. Buy buy failure. ret = {2}".format(
                self.char_id, _id, res['ret']
            ))

        # ALL OK
        # 开始操作
        if this_goods['has_limit_amount']:
            # 有每人限量的记录到每人的购买记录中
            self.mc_limit.limits[str(_id)] = self.mc_limit.limits.get(str(_id), 0) + amount
            self.mc_limit.save()

        # 更新store
        if this_goods['has_total_amount']:
            store[_id]['total_amount_run_time'] = res['data']['total_amount_run_time']


        # 扣钱
        if this_goods.sell_tp == 1:
            char.update(gold=-wealth_needs, des='Store Buy {0} * {1}. Cost'.format(_id, amount))
        else:
            char.update(sycee=-wealth_needs, des='Store Buy {0} * {1}. Cost'.format(_id, amount))


        # 给东西
        item = Item(self.char_id)
        if this_goods['item_tp'] == 1:
            save_hero(self.char_id, [this_goods['item_id']] * amount)
        elif this_goods.item_tp == 2:
            for i in range(amount):
                item.equip_add(this_goods['item_id'])
        elif this_goods.item_tp == 3:
            item.gem_add([(this_goods['item_id'], amount)])
        else:
            item.stuff_add([(this_goods['item_id'], amount)])

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
                # TODO
                # g.vip_condition.can_buy = mc.vip >= v['vip_condition']
                g.vip_condition.can_buy = False

        return msg



    def send_notify(self, store=None):
        msg = self.fill_up_notify_msg(store=store)
        publish_to_char(self.char_id, pack_msg(msg))
