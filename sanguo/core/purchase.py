# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-30'

from mongoengine import DoesNotExist

from core.resource import Resource
from core.mongoscheme import MongoPurchaseRecord
from core.msgpipe import publish_to_char
from core.exception import SanguoException

from utils.api import api_purchase_done, api_purchase_products, api_purchase_verify
from utils import pack_msg

from protomsg import PurchaseStatusNotify

from preset.data import PURCHASE
from preset import errormsg

def get_purchase_products():
    res = api_purchase_products({})
    return res['data']['products']


class VerifyResult(object):
    __slots__ = ['ret', 'product_id', 'name', 'add_sycee']
    def __init__(self, ret, product_id=None, name=None, add_sycee=None):
        self.ret = ret
        self.product_id = product_id
        self.name = name
        self.add_sycee = add_sycee


def verify_buy(char_id, receipt):
    data = {
        'char_id': char_id,
        'receipt': receipt,
    }

    # FIXME error handle
    res = api_purchase_verify(data)
    if res['ret'] != 0:
        return VerifyResult(res['ret'])

    log_id = res['data']['log_id']
    char_id = res['data']['char_id']
    product_id = res['data']['product_id']
    name = res['data']['name']
    sycee = res['data']['sycee']
    actual_sycee = res['data']['actual_sycee']

    resource = Resource(char_id, "Purchase Done", "purchase got: sycee {0}, actual sycee {1}".format(sycee, actual_sycee))
    resource.add(purchase_got=sycee, purchase_actual_got=actual_sycee)

    api_purchase_done({'log_id': log_id})

    return VerifyResult(0, product_id=product_id, name=name, add_sycee=actual_sycee)



class PurchaseAction(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.mongo_record = MongoPurchaseRecord.objects.get(id=char_id)
        except DoesNotExist:
            self.mongo_record = MongoPurchaseRecord(id=char_id)
            self.mongo_record.times = {}
            self.mongo_record.yueka_sycee = 0
            self.mongo_record.yueka_remained_days = 0
            self.mongo_record.has_unconfirmed = False
            self.mongo_record.save()


    def all_times(self):
        return {int(k): v for k, v in self.mongo_record.times.iteritems()}

    def make_purchase(self, goods_id):
        if goods_id not in PURCHASE:
            raise SanguoException(
                errormsg.PURCHASE_DOES_NOT_EXIST,
                self.char_id,
                "Purchase."
                "goods_id {0} not exist".format(goods_id)
            )

        times = self.mongo_record.times.get(str(goods_id), 0)
        self.mongo_record.times[str(goods_id)] = times + 1
        self.mongo_record.save()

        self.send_notify()


    def send_reward(self, goods_id):
        p = PURCHASE[goods_id]

        is_first = self.mongo_record.times.get(str(goods_id), 1) == 1


        if p.tp_obj.continued_days > 0:
            self.send_reward_yueka(goods_id, is_first)
        else:
            self.send_reward_sycee(goods_id, is_first)

        self.send_notify()


    def send_reward_yueka(self, goods_id, is_first):
        # 月卡
        # XXX NOTE
        # 系统只支持一种类型的月卡
        self.send_reward_sycee(goods_id, is_first)

        p = PURCHASE[goods_id]
        self.mongo_record.yueka_sycee = p.tp_obj.day_sycee
        self.mongo_record.yueka_remained_days += p.tp_obj.continued_days
        self.mongo_record.save()



    def send_reward_sycee(self, goods_id, is_first):
        # 元宝
        p = PURCHASE[goods_id]
        addition = p.first_addition_sycee if is_first else p.addition_sycee

        purchase_got = p.sycee
        purchase_actual_got = purchase_got + addition

        resource = Resource(self.char_id, "Purchase")
        resource.add(purchase_got=purchase_got, purchase_actual_got=purchase_actual_got)


    def send_notify(self):
        msg = PurchaseStatusNotify()
        times = self.all_times()

        for _id in PURCHASE.keys():
            s = msg.status.add()
            s.id = _id
            s.first = _id in times

        msg.yueka_remained_days = self.mongo_record.yueka_remained_days

        publish_to_char(self.char_id, pack_msg(msg))

