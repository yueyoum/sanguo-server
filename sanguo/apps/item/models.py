# -*- coding: utf-8 -*-
from django.db import models


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



class EquipmentClass(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=8)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'equip_type'
        verbose_name = "装备类别"
        verbose_name_plural = "装备类别"


class Equipment(models.Model):
    EQUIP_TYPE = (
        (1, "武器"),
        (2, "防具"),
        (3, "饰品"),
    )

    id = models.IntegerField(primary_key=True)
    name = models.CharField("名字", max_length=16)
    icon = models.IntegerField("图标ID", blank=True, null=True)
    icon_large = models.IntegerField("大图标ID", blank=True, null=True)
    step = models.SmallIntegerField("阶")

    tp = models.SmallIntegerField("类型", choices=EQUIP_TYPE)
    cls = models.ForeignKey(EquipmentClass, verbose_name="类别")

    upgrade_to = models.CharField("升级到", max_length=255, blank=True)
    stuff_needs = models.CharField("所需材料", max_length=255, blank=True)

    attack = models.IntegerField("攻击", default=0)
    defense = models.IntegerField("防御", default=0)
    hp = models.IntegerField("生命", default=0)

    slots = models.SmallIntegerField("孔数")
    gem_addition = models.IntegerField("宝石属性加成")

    def __unicode__(self):
        return u'<装备: %s>' % self.name

    class Meta:
        db_table = 'equipment'
        verbose_name = "装备"
        verbose_name_plural = "装备"

