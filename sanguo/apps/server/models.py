# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.signals import post_delete, post_save
from django.utils import timezone

from utils import cache

SERVER_CACHE_KEY = 'servers'


class Server(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=32)

    create_at = models.DateTimeField(default=timezone.now())
    active = models.BooleanField(default=True)

    class Meta:
        db_table = 'server'

    @staticmethod
    def servers():
        s = cache.get(SERVER_CACHE_KEY)
        if s:
            return s

        return _set_server_cache()


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


def _set_server_cache():
    servers = Server.objects.all()
    data = {}
    for s in servers:
        data[s.id] = s
    cache.set(SERVER_CACHE_KEY, data, hours=None)
    return data


def _server_post_save_callback(sender, instance, created, **kwargs):
    if created:
        ServerStatus.objects.create(server=instance)

    _set_server_cache()

def _server_post_delete_callback(sender, instance, **kwargs):
    _set_server_cache()


post_save.connect(
    _server_post_save_callback,
    sender=Server,
    dispatch_uid='apps.server.Server.post_save'
)

post_delete.connect(
    _server_post_delete_callback,
    sender=Server,
    dispatch_uid='apps.server.Server.post_delete'
)

