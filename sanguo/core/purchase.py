# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-30'

import time
import json

from mongoengine import DoesNotExist
from core.server import server
from core.resource import Resource
from core.mongoscheme import MongoPurchaseRecord
from core.msgpipe import publish_to_char
from core.exception import SanguoException
from core.mail import Mail
from core.attachment import get_drop
from utils.api import api_purchase_verify, api_purchase91_confirm, api_purchase_aiyingyong_confirm, api_purchase_allsdk_verify, api_purchase_jodoplay_confirm
from utils import pack_msg
from protomsg import PurchaseStatusNotify, PurchaseConfirmResponse
from preset.data import PURCHASE
from preset.settings import PURCHASE_FIRST_REWARD_PACKAGE_IDS, MAIL_PURCHASE_FIRST_CONTENT, MAIL_PURCHASE_FIRST_TITLE
from preset import errormsg


class YuekaLockTimeOut(Exception):
    pass


class BasePurchaseAction(object):
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
            self.mongo_record.save()


    def all_times(self):
        return {int(k): v for k, v in self.mongo_record.times.iteritems()}


    def send_reward(self, goods_id):
        p = PURCHASE[goods_id]

        first = len(self.mongo_record.times) == 0

        buy_times = self.mongo_record.times.get(str(goods_id), 0)
        is_first = buy_times == 0

        if p.tp_obj.continued_days > 0:
            self.send_reward_yueka(goods_id, is_first)
        else:
            self.send_reward_sycee(goods_id, is_first)

        self.mongo_record.times[str(goods_id)] = buy_times + 1
        self.mongo_record.save()

        self.send_notify()

        title = u'充值成功'
        content = u'获得了: {0}'.format(p.first_des if is_first else p.des)
        mail = Mail(self.char_id)
        mail.add(title, content)

        # 首冲奖励
        if first:
            self.send_first_reward()


    def send_first_reward(self):
        standard_drop = get_drop(PURCHASE_FIRST_REWARD_PACKAGE_IDS)

        mail = Mail(self.char_id)
        mail.add(
            MAIL_PURCHASE_FIRST_TITLE,
            MAIL_PURCHASE_FIRST_CONTENT,
            attachment=json.dumps(standard_drop)
        )


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
            s.first = _id not in times

        msg.yueka_remained_days = self.mongo_record.yueka_remained_days

        publish_to_char(self.char_id, pack_msg(msg))


    def check_confirm(self):
        # for third platform
        api = self.get_confirm_api()

        res = api(data={'char_id': self.char_id})
        print "==== PURCHASE CONFIRM ===="
        print res

        response = PurchaseConfirmResponse()
        response.ret = res['ret']
        if res['ret']:
            response.reason = res['data']['status']

        response.goods_id = res['data']['goods_id']
        return response

    def get_confirm_api(self):
        raise NotImplementedError()



class PurchaseAction91(BasePurchaseAction):
    def get_confirm_api(self):
        return api_purchase91_confirm


class PurchaseActioinAiyingyong(BasePurchaseAction):
    def get_confirm_api(self):
        return api_purchase_aiyingyong_confirm


class PurchaseActionJodoplay(BasePurchaseAction):
    def get_confirm_api(self):
        return api_purchase_jodoplay_confirm

    def send_reward_with_custom_price(self, goods_id, price):
        # 这里 price 是新台币，而且不一定是这个goods_id所对应的价格
        # 所以这里按照比例给东西
        p = PURCHASE[goods_id]

        xintaibi = p.rmb * 5

        buy_div, buy_mod = divmod(price, xintaibi)
        for i in xrange(buy_div):
            self.send_reward(goods_id)

        if buy_mod:
            # 换算成对应的元宝
            sycee = buy_mod * 2

            resource = Resource(self.char_id, "Purchase With Custom Price")
            resource.add(purchase_got=sycee, purchase_actual_got=sycee)

            title = u'充值成功'
            content = u'獲得了 {0} 元寶'.format(sycee)
            mail = Mail(self.char_id)
            mail.add(title, content)





class PurchaseActionIOS(BasePurchaseAction):
    def check_verify(self, receipt):
        data = {
            'server_id': server.id,
            'char_id': self.char_id,
            'receipt': receipt
        }
        res = api_purchase_verify(data)
        if res['ret'] == errormsg.PURCHASE_ALREADY_VERIFIED:
            # 已经验证过的，客户端当作成功返回，只是不给东西
            return 0

        if res['ret'] != 0:
            raise SanguoException(
                res['ret'],
                self.char_id,
                "Purchase IOS Verify",
                "api_purchase_verify, ret = {0}".format(res['ret'])
            )

        # OK
        goods_id = res['data']['goods_id']
        self.send_reward(goods_id)

        return goods_id


class PurchaseActionAllSDk(BasePurchaseAction):
    def check_verify(self, sn, goods_id, platform):
        data = {
            'server_id': server.id,
            'char_id': self.char_id,
            'sn': sn,
            'goods_id': goods_id,
            'platform': platform
        }

        res = api_purchase_allsdk_verify(data)

        if res['ret'] == errormsg.PURCHASE_ALREADY_VERIFIED:
            return 0

        if res['ret'] != 0:
            raise SanguoException(
                res['ret'],
                self.char_id,
                "Purchase AllSDK Verify",
                "api_purchase_allsdk_verify, ret = {0}".format(res['ret'])
            )

        goods_id_returned = res['data']['goods_id']
        self.send_reward(goods_id_returned)
        return goods_id_returned
