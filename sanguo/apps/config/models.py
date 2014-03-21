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
        data = cache.get('charinit')
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

    cache.set('charinit', data, expire=None)
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


# 比武排名奖励
class ArenaReward(models.Model):
    id = models.IntegerField("排名级别", primary_key=True)
    name = models.CharField("称谓", max_length=32, blank=True)
    day_gold = models.IntegerField("日金币")
    week_gold = models.IntegerField("周金币")
    week_stuffs = models.CharField("周材料", max_length=255, blank=True)

    class Meta:
        db_table = 'arena_reward'
        verbose_name = "比武奖励"
        verbose_name_plural = "比武奖励"
        ordering = ('id',)

    @staticmethod
    def all():
        data = cache.get('arenareward')
        if data:
            return data
        return save_arena_reward_cache()

    @staticmethod
    def cache_obj(rank, data=None):
        if not data:
            data = ArenaReward.all()
        for k, v in data.items():
            if rank >= k:
                return v


def save_arena_reward_cache(*args, **kwargs):
    rewards = ArenaReward.objects.all().order_by('-id')
    data = {r.id: r for r in rewards}
    cache.set('arenareward', data, expire=None)
    return data


post_save.connect(
    save_arena_reward_cache,
    sender=ArenaReward,
    dispatch_uid='apps.config.ArenaReward.post_save'
)

post_delete.connect(
    save_arena_reward_cache,
    sender=ArenaReward,
    dispatch_uid='apps.config.ArenaReward.post_delete'
)

# 通知消息模板
class Notify(models.Model):
    id = models.IntegerField(primary_key=True)
    template = models.CharField("模板", max_length=255)
    des = models.CharField("说明", max_length=255, blank=True)

    class Meta:
        db_table = 'notify'
        ordering = ('id',)
        verbose_name = '消息模板'
        verbose_name_plural = '消息模板'


# 功能开放
class FunctionOpen(models.Model):
    FUNC_ID = (
        (1, '装备强化'),
        (2, '装备进阶'),
        (3, '武将进阶'),
        (4, '宝石镶嵌'),
        (5, '日常任务'),
        (6, '成就任务'),
        (7, '挂机功能'),
        (8, '比武功能'),
        (9, '掠夺功能'),
        (10, '官职功能'),
        (11, '精英副本'),
        (12, '好友功能'),
        (13, '猛将挑战'),
    )

    SOCKET_AMOUNT = (
        (4, '上阵四人'),
        (5, '上阵五人'),
        (6, '上阵六人'),
        (7, '上阵七人'),
        (8, '上阵八人'),
    )

    char_level = models.IntegerField("君主等级条件", default=0)
    stage_id = models.IntegerField("关卡ID条件", default=0)

    func_id = models.IntegerField("开启功能", choices=FUNC_ID, null=True, blank=True)
    socket_amount = models.IntegerField("上阵人数", choices=SOCKET_AMOUNT, null=True, blank=True)

    class Meta:
        db_table = 'function_open'
        ordering = ('id',)
        verbose_name = '功能开启'
        verbose_name_plural = '功能开启'

