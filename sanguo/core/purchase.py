# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-30'

import time

from mongoengine import DoesNotExist

from core.resource import Resource
from core.mongoscheme import MongoPurchaseRecord
from core.msgpipe import publish_to_char
from core.exception import SanguoException

from utils.api import api_purchase_done, api_purchase_products, api_purchase_verify, api_purchase91_confirm
from utils import pack_msg

from protomsg import PurchaseStatusNotify, Purchase91ConfirmResponse

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


class YuekaLockTimeOut(Exception):
    pass



class PurchaseAction(object):
    def __init__(self, char_id):
        self.char_id = char_id
        self.load_mongo_record()

    def load_mongo_record(self):
        try:
            self.mongo_record = MongoPurchaseRecord.objects.get(id=self.char_id)
        except DoesNotExist:
            self.mongo_record = MongoPurchaseRecord(id=self.char_id)
            self.mongo_record.times = {}
            self.mongo_record.yueka_sycee = 0
            self.mongo_record.yueka_remained_days = 0
            self.mongo_record.yueka_lock = False
            self.mongo_record.has_unconfirmed = False
            self.mongo_record.save()


    def all_times(self):
        return {int(k): v for k, v in self.mongo_record.times.iteritems()}


    def set_has_unconfirmed(self):
        self.mongo_record.has_unconfirmed = True
        self.mongo_record.save()


    def check_confirm(self):
        res = api_purchase91_confirm(data={'char_id': self.char_id})
        print "91 confirm"
        print res

        self.mongo_record.has_unconfirmed = res['data']['has_unconfirmed']
        self.mongo_record.save()

        if res['ret'] == 0 and res['data']['goods_id']:
            self.send_reward(res['data']['goods_id'])

        response = Purchase91ConfirmResponse()
        response.ret = res['ret']
        if res['ret']:
            response.reason = res['data']['reason']

        response.goods_id = res['data']['goods_id']
        return response


    def send_confirm_response(self):
        msg = self.check_confirm()
        publish_to_char(self.char_id, pack_msg(msg))


    def login_process(self):
        if self.mongo_record.has_unconfirmed:
            self.send_confirm_response()


    def send_reward(self, goods_id):
        p = PURCHASE[goods_id]

        buy_times = self.mongo_record.times.get(str(goods_id), 0)
        is_first = buy_times == 0

        if p.tp_obj.continued_days > 0:
            self.send_reward_yueka(goods_id, is_first)
        else:
            self.send_reward_sycee(goods_id, is_first)

        self.mongo_record.times[str(goods_id)] = buy_times + 1
        self.mongo_record.save()

        self.send_notify()


    def send_reward_yueka(self, goods_id, is_first):
        # 月卡
        # XXX NOTE
        # 系统只支持一种类型的月卡
        self.send_reward_sycee(goods_id, is_first)

        p = PURCHASE[goods_id]

        try:
            self.set_yueka_remained_days(p.tp_obj.continued_days)
        except YuekaLockTimeOut:
            raise SanguoException(
                errormsg.PURCHASE_91_FAILURE,
                self.char_id,
                "Purchase",
                "get yueka lock timeout..."
            )

        self.mongo_record.yueka_sycee = p.tp_obj.day_sycee
        self.mongo_record.save()


    def set_yueka_remained_days(self, add_days):
        for i in range(10):
            self.load_mongo_record()
            if not self.mongo_record.yueka_lock:
                self.mongo_record.yueka_lock = True
                self.mongo_record.save()
                break
            else:
                time.sleep(0.2)
        else:
            raise YuekaLockTimeOut()

        self.mongo_record.yueka_remained_days += add_days
        if self.mongo_record.yueka_remained_days < 0:
            self.mongo_record.yueka_remained_days = 0

        self.mongo_record.yueka_lock = False
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

