# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-30'


from core.purchase import get_purchase_products, verify_buy
from utils.decorate import message_response

from libs import pack_msg
from protomsg import GetProductsResponse, BuyVerityResponse

@message_response("GetProductsResponse")
def products(request):
    response = GetProductsResponse()
    response.ret = 0

    data = get_purchase_products()
    for k, v in data.iteritems():
        p = response.products.add()
        p.id = int(k)
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
