# -*- coding: utf-8 -*-
from django.db import models

class Equipment(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField("名字", max_length=16)
    icon = models.CharField("图标ID", max_length=32, blank=True)
    icon_large = models.CharField("大图标ID", max_length=32, blank=True)

    step = models.SmallIntegerField("阶")
    step_name = models.CharField("阶名字", max_length=12)

    tp = models.SmallIntegerField("类型")
    tp_name = models.CharField("类型名字", max_length=12)

    cls = models.SmallIntegerField("类别")
    cls_name = models.CharField("类别名字", max_length=12)

    upgrade_to = models.IntegerField("升级到", null=True, blank=True)
    stuff_needs = models.CharField("所需材料", max_length=255, blank=True)

    attack = models.IntegerField("攻击", default=0)
    defense = models.IntegerField("防御", default=0)
    hp = models.IntegerField("生命", default=0)

    slots = models.SmallIntegerField("孔数")
    gem_addition = models.IntegerField("宝石属性加成")

    growing = models.IntegerField("成长系数")

    def __unicode__(self):
        return u'<装备: %s>' % self.name


    class Meta:
        db_table = 'equipment'
        ordering = ('id',)
        verbose_name = "装备"
        verbose_name_plural = "装备"



class Gem(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField("名字", max_length=16)
    icon = models.CharField("图标", max_length=32, blank=True)
    tp_name = models.CharField("类型名字", max_length=16)
    level = models.IntegerField("等级")

    used_for = models.CharField("用于", max_length=16)
    used_for_name = models.CharField("用于名字", max_length=16)
    value = models.IntegerField("数值")

    merge_to = models.IntegerField("合成到", null=True, blank=True)

    sell_gold = models.IntegerField("售卖所的金币")

    def __unicode__(self):
        return u'<宝石: %s>' % self.name


    class Meta:
        db_table = 'gem'
        ordering = ('id',)
        verbose_name = "宝石"
        verbose_name_plural = "宝石"


class Stuff(models.Model):
    TYPE = (
        (1, '材料'),
        (2, '宝物'),
    )

    id = models.IntegerField(primary_key=True)
    name = models.CharField("名字", max_length=16)
    icon = models.CharField("图标", max_length=255, blank=True)
    des = models.CharField("描述", max_length=255, blank=True)
    buy_sycee = models.IntegerField("购买需要元宝")
    sell_gold = models.IntegerField("售卖所得金币")

    tp = models.IntegerField("类型", choices=TYPE)
    value = models.IntegerField("值", null=True, blank=True)

    def __unicode__(self):
        return u'<材料: %s>' % self.name


    class Meta:
        db_table = 'stuff'
        ordering = ('id',)
        verbose_name = "道具"
        verbose_name_plural = "道具"

