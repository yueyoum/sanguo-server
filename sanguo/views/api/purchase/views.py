# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-7-30'


from utils.decorate import json_return
from core.purchase import PurchaseAction91, PurchaseActioinAiyingyong, PurchaseActionJodoplay, BasePurchaseAction
from preset.data import PURCHASE

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

@json_return
def purchase_aiyingyong_done(request):
    try:
        char_id = int(request.POST['char_id'])
        goods_id = int(request.POST['goods_id'])
    except:
        return {'ret': 1}

    p = PurchaseActioinAiyingyong(char_id)
    p.send_reward(goods_id)

    return {'ret': 0}

@json_return
def purchase_jodoplay_done(request):
    try:
        char_id = int(request.POST['char_id'])
        goods_id = int(request.POST['goods_id'])
        price = int(request.POST['price'])
    except:
        return {'ret': 1}

    print "char_id: {0}, goods_id: {1}, price: {2}".format(char_id, goods_id, price)

    p = PurchaseActionJodoplay(char_id)
    p.send_reward_with_custom_price(goods_id, price)
    return {'ret': 0}

@json_return
def purchase_self(request):
    # 自身充值
    try:
        char_id = int(request.POST['char_id'])
        goods_id = int(request.POST['goods_id'])
        amount = int(request.POST['amount'])
    except:
        return {'ret': 1}

    for i in range(amount):
        p = BasePurchaseAction(char_id)
        p.send_reward(goods_id)

    # 额外赠送30%
    addition_sycee = PURCHASE[goods_id].sycee * amount * 0.3
    p = BasePurchaseAction(char_id)
    p.send_addition_sycee_via_mail(int(addition_sycee))

    return {'ret': 0}
