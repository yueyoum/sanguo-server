# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-7-30'


from utils.decorate import json_return
from core.purchase import PurchaseAction91

@json_return
def purchase91_done(request):
    try:
        char_id = int(request.POST['char_id'])
        goods_id = int(request.POST['goods_id'])
    except:
        return {'ret': 1}

    p = PurchaseAction91(char_id)
    p.send_reward(goods_id)

    return {'ret': 0}
