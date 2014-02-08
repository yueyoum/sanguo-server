# -*- coding: utf-8 -*-

from django.db import models

from utils import cache

class AchievementCondition(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField("名称", max_length=32)

    def __unicode(self):
        return u'<成就条件: %s>' % self.name

    class Meta:
        db_table = 'achievement_condition'
        verbose_name = "成就条件"
        verbose_name_plural = "成就条件"


class Achievement(models.Model):
    id = models.IntegerField(primary_key=True)
    tp = models.IntegerField("类型")
    tp_name = models.CharField("类型名字", max_length=32)
    name = models.CharField("成就名称", max_length=32)
    des = models.TextField("描述", blank=True)

    condition = models.ForeignKey(AchievementCondition, verbose_name="条件")
    condition_value = models.CharField("条件值", max_length=255)

    sycee = models.IntegerField("奖励元宝", null=True, blank=True)
    buff_tp = models.IntegerField("BUFF_ID", null=True, blank=True)
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


