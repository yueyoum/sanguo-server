# -*- coding: utf-8 -*-

from django.db import models

from utils import cache


class Achievement(models.Model):
    MODE = (
        (1, '多个ID条件'),
        (2, '单个ID条件'),
        (3, '数量条件'),
    )
    id = models.IntegerField(primary_key=True)
    tp = models.IntegerField("类型")
    tp_name = models.CharField("类型名字", max_length=32)
    name = models.CharField("成就名称", max_length=32)
    des = models.TextField("描述", blank=True)

    mode = models.IntegerField("条件类型", choices=MODE)

    condition_id = models.IntegerField("条件ID")
    condition_name = models.CharField("条件名称", max_length=32)
    condition_value = models.CharField("条件值", max_length=255)

    sycee = models.IntegerField("奖励元宝", null=True, blank=True)
    buff_id = models.IntegerField("BUFF_ID", null=True, blank=True)
    buff_name = models.CharField("BUFF名称", max_length=32, blank=True)
    buff_value = models.IntegerField("BUFF值", null=True, blank=True)

    def __unicode__(self):
        return u'<成就: %s>' % self.name

    class Meta:
        db_table = 'achievement'
        ordering = ('id',)
        verbose_name = "成就"
        verbose_name_plural = "成就"

    @staticmethod
    def all():
        data = cache.get('achievement', hours=None)
        if data:
            return data
        return save_achievement_cache()



def save_achievement_cache(*args, **kwargs):
    achieves = Achievement.objects.all()
    data = {a.id: a for a in achieves}
    cache.set('achievement', data, hours=None)
    return data


