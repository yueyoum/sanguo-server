# -*- coding: utf-8 -*-
from django.db import models
from django.db.models.signals import post_delete, post_save
from utils import cache


class EquipUpdateProcess(object):
    __slots__ = ['processes', ]

    def __init__(self):
        self.processes = []

    def __iter__(self):
        for p in self.processes:
            yield p


    def add(self, data):
        self.processes.append(data)

    @property
    def end(self):
        end = self.processes[-1]
        return end[0], end[1]




class Equipment(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField("名字", max_length=16)
    icon = models.IntegerField("图标ID", blank=True, null=True)
    icon_large = models.IntegerField("大图标ID", blank=True, null=True)

    step = models.SmallIntegerField("阶")
    step_name = models.CharField("阶名字", max_length=12)

    tp = models.SmallIntegerField("类型")
    tp_name = models.CharField("类型名字", max_length=12)

    cls = models.SmallIntegerField("类别")
    cls_name = models.CharField("类别名字", max_length=12)

    upgrade_to = models.CharField("升级到", max_length=255, blank=True)
    stuff_needs = models.CharField("所需材料", max_length=255, blank=True)

    attack = models.IntegerField("攻击", default=0)
    defense = models.IntegerField("防御", default=0)
    hp = models.IntegerField("生命", default=0)

    slots = models.SmallIntegerField("孔数")
    gem_addition = models.IntegerField("宝石属性加成")

    growing = models.IntegerField("成长系数")

    def __unicode__(self):
        return u'<装备: %s>' % self.name

    @staticmethod
    def all():
        data = cache.get('equip', hours=None)
        if data:
            return data
        return _set_equip_cache()

    class Meta:
        db_table = 'equipment'
        ordering = ('id',)
        verbose_name = "装备"
        verbose_name_plural = "装备"


def _set_equip_cache():
    equips = Equipment.objects.all()
    data = {e.id: e for e in equips}
    cache.set('equip', data, hours=None)
    return data


def _update_equip_cache(*args, **kwargs):
    _set_equip_cache()

post_save.connect(
    _update_equip_cache,
    sender=Equipment,
    dispatch_uid='apps.item.Equipment.post_save'
)

post_delete.connect(
    _update_equip_cache,
    sender=Equipment,
    dispatch_uid='apps.item.Equipment.post_save'
)



class Stuff(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField("名字", max_length=16)
    icon = models.IntegerField("图标ID", blank=True, null=True)
    des = models.CharField("描述", max_length=255, blank=True)

    def __unicode__(self):
        return u'<材料: %s>' % self.name

    class Meta:
        db_table = 'stuff'
        ordering = ('id',)
        verbose_name = "材料"
        verbose_name_plural = "材料"
