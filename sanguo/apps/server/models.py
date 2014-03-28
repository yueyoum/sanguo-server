# -*- coding: utf-8 -*-

from django.db import models
from django.utils import timezone




class Server(models.Model):
    id = models.IntegerField("ID", primary_key=True)
    name = models.CharField("名字", max_length=32)

    create_at = models.DateTimeField("创建于")
    active = models.BooleanField("开启", default=True)

    def __unicode__(self):
        return u'%d - %s' % (self.id, self.name)

    class Meta:
        db_table = 'server'
        verbose_name = "服务器"
        verbose_name_plural = "服务器"


    def save(self, *args, **kwargs):
        if not self.create_at:
            self.create_at = timezone.now()
        super(Server, self).save(*args, **kwargs)


class ServerStatus(models.Model):
    server = models.OneToOneField(Server)
    # 角色总数
    char_amount = models.IntegerField(default=0)
    # 总登录次数
    login_times = models.IntegerField(default=0)
    # 付费总人数
    pay_players_amount = models.IntegerField(default=0)
    # 付费总数
    pay_total = models.IntegerField(default=0)

    pve_times = models.IntegerField(default=0)
    pvp_times = models.IntegerField(default=0)

    class Meta:
        db_table = 'server_status'

