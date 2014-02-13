# -*- coding: utf-8 -*-

from django.db import models
from utils import cache

class Official(models.Model):
    id = models.IntegerField("等级", primary_key=True)
    name = models.CharField("名称", max_length=32)
    exp_needs = models.IntegerField("升级所需经验")
    gold = models.IntegerField("每日可领取金币")

    class Meta:
        db_table = 'official'
        ordering = ('id',)
        verbose_name = '官职'
        verbose_name_plural = '官职'

    def __unicode__(self):
        return u'<Official: %s>' % self.name

    @staticmethod
    def all():
        data = cache.get('official', hours=None)
        if data:
            return data
        return save_offical_cache()


def save_offical_cache(*args, **kwargs):
    offs = Official.objects.all()
    data = {o.id: o for o in offs}
    cache.set('official', data, hours=None)
    return data


