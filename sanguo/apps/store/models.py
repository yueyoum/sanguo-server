# -*- coding: utf-8 -*-

from django.db import models

from utils import cache


STORE_TAG = (
    (1, '促销'),
    (2, '抢购'),
    (3, '商城'),
    (4, 'VIP专卖'),
    (5, '装备'),
)

STORE_ITEM_TP = (
    (1, '武将'),
    (2, '装备'),
    (3, '宝石'),
    (4, '材料'),
    (5, '金币'),
)

STORE_SELL_TP = (
    (1, '金币'),
    (2, '元宝'),
)



class Store(models.Model):
    id = models.IntegerField(primary_key=True)
    tag_id = models.IntegerField("标签", choices=STORE_TAG)

    item_tp = models.IntegerField("类型", choices=STORE_ITEM_TP)
    item = models.IntegerField("物品")

    sell_tp = models.IntegerField("售卖类型", choices=STORE_SELL_TP)
    original_price = models.IntegerField("原价")
    sell_price = models.IntegerField("售价")

    total_amount = models.IntegerField("总量", default=0, help_text='0表示没有限制')
    limit_amount = models.IntegerField("每人每天限够", default=0, help_text='0表示没有限制')

    vip_condition = models.IntegerField("VIP等级需求", default=0, help_text='多少级VIP以上才能购买')
    char_level = models.IntegerField("君主等级")

    class Meta:
        db_table = 'store'
        verbose_name = "商城"
        verbose_name_plural = "商城"

    @staticmethod
    def all():
        data = cache.get('store')
        if data:
            return data
        return save_store_cache()

    @staticmethod
    def update_cache():
        return save_store_cache()



def save_store_cache(*args, **kwargs):
    ss = Store.objects.all()
    data = {s.id: s for s in ss}
    cache.set('store', data, expire=None)
    return data


class StoreBuyLog(models.Model):
    STATUS = (
        (1, '订单'),
        (2, '付款'),
        (3, '完成')
    )
    order_id = models.CharField("订单ID", max_length=255, db_index=True)
    char_id = models.IntegerField("角色ID", db_index=True)
    tag_id = models.IntegerField("标签", choices=STORE_TAG)
    item_tp = models.IntegerField("类型", choices=STORE_ITEM_TP)
    item = models.IntegerField("物品")
    sell_tp = models.IntegerField("售卖类型", choices=STORE_SELL_TP)
    sell_price = models.IntegerField("售价")
    amount = models.IntegerField("购买数量")
    buy_time = models.DateTimeField("购买时间")
    status = models.IntegerField("状态", choices=STATUS)

    class Meta:
        db_table = 'store_log'
        ordering = ('-id',)
        verbose_name = "商城购买日志"
        verbose_name_plural = "商城购买日志"
