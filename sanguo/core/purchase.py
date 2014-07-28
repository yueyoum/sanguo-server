# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-30'

from mongoengine import DoesNotExist

from core.resource import Resource
from core.mongoscheme import MongoPurchaseRecord
from core.msgpipe import publish_to_char

from utils.api import api_purchase_done, api_purchase_products, api_purchase_verify
from utils import pack_msg

from protomsg import PurchaseStatusNotify

from preset.data import PURCHASE

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
            self.mongo_record.times = {}
            self.mongo_record.save()

    def all_times(self):
        return {int(k): v for k, v in self.mongo_record.times.iteritems()}

    def send_notify(self):
        msg = PurchaseStatusNotify()
        times = self.all_times()

        for _id in PURCHASE.keys():
            s = msg.status.add()
            s.id = _id
            s.first = _id in times

        publish_to_char(self.char_id, pack_msg(msg))

