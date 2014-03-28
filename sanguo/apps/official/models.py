# -*- coding: utf-8 -*-

from django.db import models

class Official(models.Model):
    id = models.IntegerField("等级", primary_key=True)
    name = models.CharField("名称", max_length=32)
    gold = models.IntegerField("每日可领取金币")
    # stuffs = models.CharField("升级道具奖励", max_length=255, blank=True,
    #                                   help_text='id:amount,id:amount'
    #                                   )

    class Meta:
        db_table = 'official'
        ordering = ('id',)
        verbose_name = '官职'
        verbose_name_plural = '官职'

    def __unicode__(self):
        return u'<Official: %s>' % self.name

