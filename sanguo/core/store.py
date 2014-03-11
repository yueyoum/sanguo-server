# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/20/14'

from mongoengine import DoesNotExist

from django.utils import timezone as dj_timezone

from apps.store.models import Store as ModelStore, StoreBuyLog
from core.mongoscheme import MongoStoreAmount, MongoStoreCharLimit
from core.msgpipe import publish_to_char
from core.character import Char
from core.item import Item
from core.hero import save_hero
from core.exception import InvalidOperate, GoldNotEnough, SyceeNotEnough

from utils import pack_msg
from utils.functional import timebased_unique_id

from protomsg import StoreNotify

class Store(object):
    def __init__(self, char_id):
        self.char_id = char_id

    def buy(self, _id, amount):
        try:
            this_goods = ModelStore.all()[_id]
        except KeyError:
            raise InvalidOperate("Store Buy. Char {0} Try to buy a NONE exist goods {1}".format(self.char_id, _id))

        char = Char(self.char_id)
        cache_char = char.cacheobj

        if this_goods.sell_tp == 1:
            if cache_char.gold < this_goods.sell_price * amount:
                raise GoldNotEnough("Store Buy. Char {0} try to buy {1}. But gold not enough".format(self.char_id, _id))
        else:
            if cache_char.sycee < this_goods.sell_price * amount:
                raise SyceeNotEnough("Store Buy. Char {0} try to buy {1}. But sycee not enough".format(self.char_id, _id))

        # TODO 检查背包是否满呢


        if this_goods.limit_amount > 0:
            # 每人每天限量
            try:
                mongo_limit = MongoStoreCharLimit.objects.get(id=self.char_id)
            except DoesNotExist:
                mongo_limit = MongoStoreCharLimit(id=self.char_id)
            else:
                already_buy_amount = mongo_limit.limits.get(str(_id), 0)
                if already_buy_amount + amount > this_goods.limit_amount:
                    raise InvalidOperate("Store Buy. Char {0} Try to buy goods {1}. But char has reached the buy limits {2}".format(
                        self.char_id, _id, already_buy_amount
                    ))


        if this_goods.total_amount > 0:
            # 有总量的商品
            remained_amount = this_goods.total_amount - self.sold_amount(_id)
            if remained_amount < amount:
                raise InvalidOperate("Store Buy. Char {0} Try to buy goods {1}, amount {2} > remained amount {3}".format(
                    self.char_id, _id, amount, remained_amount
                ))


        # 检查完毕 开始操作
        if this_goods.limit_amount > 0:
            # 有每人限量的记录到每人的购买记录中
            mongo_limit.limits[str(_id)] = mongo_limit.limits.get(str(_id), 0) + amount
            mongo_limit.save()

        if this_goods.total_amount > 0:
            # 有总量的商品记录购买数量
            try:
                mongo_store_amount = MongoStoreAmount.objects.get(id=_id)
            except DoesNotExist:
                mongo_store_amount = MongoStoreAmount(id=_id, sold_amount=0)

            mongo_store_amount.sold_amount += amount
            mongo_store_amount.save()

        # 购买日志
        order_id = '{0}-{1}'.format(timebased_unique_id(), str(self.char_id).zfill(10))
        buy_log = StoreBuyLog.objects.create(
            order_id = order_id,
            char_id = self.char_id,
            tag_id = this_goods.tag_id,
            item_tp = this_goods.item_tp,
            item = this_goods.item,
            sell_tp = this_goods.sell_tp,
            sell_price =this_goods.sell_price,
            amount = amount,
            buy_time = dj_timezone.now(),
            status = 1,
        )

        # 扣钱
        if this_goods.sell_tp == 1:
            char.update(gold=-this_goods.sell_price * amount, des='Store Buy. Cost')
        else:
            char.update(sycee=-this_goods.sell_price * amount, des='Store Buy. Cost')

        buy_log.status = 2
        buy_log.save()

        # 给东西
        item = Item(self.char_id)
        if this_goods.item_tp == 1:
            save_hero(self.char_id, [this_goods.item] * amount)
        elif this_goods.item_tp == 2:
            for i in range(amount):
                item.equip_add(this_goods.item)
        elif this_goods.item_tp == 3:
            item.gem_add([(this_goods.item, amount)])
        elif this_goods.item_tp == 4:
            item.stuff_add([(this_goods.item, amount)])
        else:
            char.update(gold=this_goods.item * amount, des='Store Buy. Buy Gold')

        buy_log.status = 3
        buy_log.save()

        self.send_notify()


    def sold_amount(self, _id):
        try:
            this_goods = MongoStoreAmount.objects.get(id=_id)
            sold_amount = this_goods.sold_amount
        except DoesNotExist:
            sold_amount = 0
        return sold_amount

    def _fill_up_one_goods(self, msg, goods):
        msg.id = goods.id
        msg.tag = goods.tag_id
        msg.item_tp = goods.item_tp
        msg.item = goods.item
        msg.sell_tp = goods.sell_tp
        msg.original_price = goods.original_price
        msg.sell_price = goods.sell_price

        if goods.total_amount:
            msg.total_amount = goods.total_amount - self.sold_amount(goods.id)
        else:
            msg.total_amount = 0
        msg.limit_amount = goods.limit_amount
        msg.vip_condition = goods.vip_condition

    def fill_up_notify_msg(self):
        goods = ModelStore.all()
        msg = StoreNotify()
        for g in goods.values():
            msg_g = msg.goods.add()
            self._fill_up_one_goods(msg_g, g)

        return msg


    def send_notify(self):
        msg = self.fill_up_notify_msg()
        publish_to_char(self.char_id, pack_msg(msg))
