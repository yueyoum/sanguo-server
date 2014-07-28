# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-30'


from core.purchase import get_purchase_products, verify_buy
from core.exception import SanguoException
from utils.decorate import message_response
from utils.api import api_purchase91_get_order_id, api_purchase91_confirm, api_purchase91_success91

from libs import pack_msg
from protomsg import GetProductsResponse, BuyVerityResponse, Purchase91GetOrderIdResponse, Purchase91ConfirmResponse
from preset import errormsg

from preset.data import PURCHASE

@message_response("GetProductsResponse")
def products(request):
    response = GetProductsResponse()
    response.ret = 0

    data = get_purchase_products()
    for k, v in data.iteritems():
        p = response.products.add()
        p.id = k
        p.name = v['name']
        p.des = v['des']

    return pack_msg(response)


@message_response("BuyVerityResponse")
def verify(request):
    req = request._proto
    res = verify_buy(request._char_id, req.receipt)

    response = BuyVerityResponse()
    response.ret = res.ret
    if response.ret:
        return pack_msg(response)

    response.name = res.name
    response.add_sycee = res.add_sycee
    return pack_msg(response)


@message_response("Purchase91GetOrderIdResponse")
def get_91_order_id(request):
    req = request._proto

    goods_id = req.goods_id
    if goods_id not in PURCHASE:
        raise SanguoException(
            errormsg.PURCHASE_DOES_NOT_EXIST,
            request._char_id,
            "Purchase 91. Get Order Id",
            "goods_id {0} not exist".format(goods_id)
        )

    data = {
        'char_id': request._char_id,
        'goods_id': goods_id,
    }

    try:
        res = api_purchase91_get_order_id(data=data)
    except:
        raise SanguoException(
            errormsg.PURCHASE_91_FAILURE,
            request._char_id,
            "Purchase 91. Get Order Id",
            "api_purchase91_get_order_id, failure"
        )

    if res['ret'] != 0:
        raise SanguoException(
            res['ret'],
            request._char_id,
            "Purchase 91. Get Order Id",
            "get order id failure."
        )

    response = Purchase91GetOrderIdResponse()
    response.ret = 0
    response.order_id = res['data']['order_id']
    return pack_msg(response)

@message_response("Purchase91SuccessTo91Response")
def purchase_91_success_to_91(request):
    req = request._proto

    data = {'order_id': req.order_id}
    api_purchase91_success91(data=data)
    return None


@message_response("Purchase91ConfirmResponse")
def purchase_91_confirm(request):
    res = api_purchase91_confirm(data={})
    print "91 confirm"
    print res

    if res['ret'] == 0 and res['data']['goods_id']:
        # TODO 给东西
        pass

    response = Purchase91ConfirmResponse()
    response.ret = res['ret']
    if res['ret']:
        response.reason = res['data']['reason']

    response.goods_id = res['data']['goods_id']
    return pack_msg(response)
