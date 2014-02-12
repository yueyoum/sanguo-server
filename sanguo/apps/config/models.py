# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.signals import post_delete, post_save
from utils import cache

# 角色初始化
class CharInit(models.Model):
    gold = models.IntegerField("金币", default=0)
    sycee = models.IntegerField("元宝", default=0)

    heros = models.CharField("武将", max_length=255, help_text="武将:武器,防具,饰品|武将:武器,防具,饰品")
    gems = models.CharField("宝石", max_length=255, help_text="id:amount,id:amount,id:amount")
    stuffs = models.CharField("杂物", max_length=255, help_text="id:amount,id:amount,id:amount")

    class Meta:
        db_table = 'config_charinit'
        verbose_name = "角色初始化"
        verbose_name_plural = "角色初始化"

    @staticmethod
    def cache_obj():
        data = cache.get('charinit', hours=None)
        if data:
            return data
        return save_charinit_cache()



def save_charinit_cache(*args, **kwargs):
    data = CharInit.objects.all()[0]
    decoded_heros = {}
    for hero in data.heros.split('|'):
        hero_id, equips = hero.split(':')
        equip_ids = [int(i) for i in equips.split(',')]
        decoded_heros[int(hero_id)] = equip_ids
    data.decoded_heros = decoded_heros

    decoded_gems = []
    for gems in data.gems.split(','):
        gid, amount = gems.split(':')
        decoded_gems.append((int(gid), int(amount)))
    data.decoded_gems = decoded_gems

    decoded_stuffs = []
    for stuff in data.stuffs.split(','):
        sid, amount = stuff.split(':')
        decoded_stuffs.append((int(sid), int(amount)))
    data.decoded_stuffs = decoded_stuffs

    cache.set('charinit', data, hours=None)
    return data


post_save.connect(
    save_charinit_cache,
    sender=CharInit,
    dispatch_uid='apps.config.CharInit.post_save'
)

post_delete.connect(
    save_charinit_cache,
    sender=CharInit,
    dispatch_uid='apps.config.CharInit.post_delete'
)

