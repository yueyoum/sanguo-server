# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-30'

from core.server import server
from core.purchase import PurchaseAction91, PurchaseActionIOS, PurchaseActioinAiyingyong, PurchaseActionAllSDk, PurchaseActionJodoplay
from core.exception import SanguoException
from utils.decorate import message_response
from utils.api import api_purchase_get_order_id

from libs import pack_msg
from protomsg import PurchaseGetOrderIdResponse, PurchaseIOSVerifyResponse, PurchaseAllSDKVerifyResponse
from preset import errormsg

from preset.data import PURCHASE


@message_response("PurchaseIOSVerifyResponse")
def purchase_ios_verify(request):
    req = request._proto

    p = PurchaseActionIOS(request._char_id)
    goods_id = p.check_verify(req.receipt)

    response = PurchaseIOSVerifyResponse()
    response.ret = 0
    response.goods_id = goods_id
    return pack_msg(response)

@message_response("PurchaseAllSDKVerifyResponse")
def purchase_allsdk_verify(request):
    req = request._proto

    p = PurchaseActionAllSDk(request._char_id)
    goods_id = p.check_verify(req.sn, req.goods_id, req.platform)

    response = PurchaseAllSDKVerifyResponse()
    response.ret = 0
    response.goods_id = goods_id
    return pack_msg(response)


@message_response("PurchaseGetOrderIdResponse")
def get_order_id(request):
    req = request._proto
    goods_id = req.goods_id
    platform = req.platform

    if goods_id not in PURCHASE:
        raise SanguoException(
            errormsg.PURCHASE_DOES_NOT_EXIST,
            request._char_id,
            "Purchase. Get Order Id",
            "goods_id {0} not exist".format(goods_id)
        )

    data = {
        'server_id': server.id,
        'char_id': request._char_id,
        'goods_id': goods_id,
        'platform': platform,
    }

    try:
        res = api_purchase_get_order_id(data=data)
    except:
        raise SanguoException(
            errormsg.PURCHASE_91_FAILURE,
            request._char_id,
            "Purchase 91. Get Order Id",
            "api_purchase_get_order_id, failure"
        )

    if res['ret'] != 0:
        raise SanguoException(
            res['ret'],
            request._char_id,
            "Purchase. Get Order Id",
            "get order id failure."
        )

    response = PurchaseGetOrderIdResponse()
    response.ret = 0
    response.order_id = res['data']['order_id']
    return pack_msg(response)


@message_response("PurchaseConfirmResponse")
def purchase_confirm(request):
    req = request._proto
    char_id = request._char_id

    platform = req.platform

    if platform == '91':
        p = PurchaseAction91(char_id)
        response = p.check_confirm()
    elif platform == 'aiyingyong':
        p = PurchaseActioinAiyingyong(char_id)
        response = p.check_confirm()
    elif platform == 'jodoplay':
        p = PurchaseActionJodoplay(char_id)
        response = p.check_confirm()
    else:
        raise SanguoException(
            errormsg.BAD_MESSAGE,
            char_id,
            "Purchase Confirm",
            "Unknown platform: {0}".format(platform)
        )

    return pack_msg(response)
