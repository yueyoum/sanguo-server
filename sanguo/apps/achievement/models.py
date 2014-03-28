# -*- coding: utf-8 -*-

from django.db import models

class Achievement(models.Model):
    MODE = (
        (1, '多个ID条件'),
        (2, '单个ID条件'),
        (3, '数量条件'),
        (4, '阀值数量条件'),
        (5, '反向阀值数量条件'),
    )

    id = models.IntegerField(primary_key=True)
    tp = models.IntegerField("类型")
    tp_name = models.CharField("类型名字", max_length=32)
    name = models.CharField("成就名称", max_length=32)
    first = models.BooleanField("起始")
    next = models.IntegerField("后续", null=True, blank=True)
    des = models.TextField("描述", blank=True)

    mode = models.IntegerField("条件类型", choices=MODE)

    condition_name = models.CharField("条件名称", max_length=32)
    condition_id = models.IntegerField("条件ID")
    condition_value = models.CharField("条件值", max_length=255)

    sycee = models.IntegerField("奖励元宝", null=True, blank=True)
    buff_used_for = models.CharField("BUFF用于", max_length=32, blank=True)
    buff_name = models.CharField("BUFF名称", max_length=32, blank=True)
    buff_value = models.IntegerField("BUFF值", null=True, blank=True)

    equipments = models.CharField("装备", max_length=255, blank=True)
    gems = models.CharField("宝石", max_length=255, blank=True)
    stuffs = models.CharField("材料", max_length=255, blank=True)

    def __unicode__(self):
        return u'<成就: %s>' % self.name

    class Meta:
        db_table = 'achievement'
        ordering = ('id',)
        verbose_name = "成就"
        verbose_name_plural = "成就"

