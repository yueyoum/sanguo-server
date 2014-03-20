# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.signals import post_save, post_delete

from utils import cache


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

    equipments = models.CharField("装备", blank=True)
    gems = models.CharField("宝石", blank=True)
    stuffs = models.CharField("材料", blank=True)

    def __unicode__(self):
        return u'<成就: %s>' % self.name

    class Meta:
        db_table = 'achievement'
        ordering = ('id',)
        verbose_name = "成就"
        verbose_name_plural = "成就"

    @staticmethod
    def all():
        data = cache.get('achievement')
        if data:
            return data
        return save_achievement_cache()

    @staticmethod
    def get_all_by_conditions():
        data = cache.get('achievement_conditions')
        if data:
            return data
        save_achievement_cache()
        return cache.get('achievement_conditions')


    @staticmethod
    def first_ids():
        data = cache.get('achievement_first_ids')
        if data:
            return data
        save_achievement_cache()
        return cache.get('achievement_first_ids')



    def decoded_condition_value(self):
        if self.mode == 1:
            return [int(i) for i in self.condition_value.split(',')]
        return int(self.condition_value)



def save_achievement_cache(*args, **kwargs):
    achieves = Achievement.objects.all()
    data = {}
    conditions = {}
    first_ids = []
    for a in achieves:
        data[a.id] = a
        conditions.setdefault(a.condition_id, []).append(a)
        if a.first:
            first_ids.append(a.id)

    cache.set('achievement', data, expire=None)
    cache.set('achievement_conditions', conditions, expire=None)
    cache.set('achievement_first_ids', first_ids, expire=None)
    return data


post_save.connect(
    save_achievement_cache,
    sender=Achievement,
    dispatch_uid='apps.achievement.Achievement.post_save'
)

post_delete.connect(
    save_achievement_cache,
    sender=Achievement,
    dispatch_uid='apps.achievement.Achievement.post_delete'
)

