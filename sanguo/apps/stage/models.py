# -*- coding: utf-8 -*-

import random
from django.db import models
from django.db.models.signals import post_delete, post_save

from utils import cache

class Battle(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField("名字", max_length=32)
    level_limit = models.IntegerField("等级限制", default=1)

    @staticmethod
    def all():
        data = cache.get('battle', hours=None)
        if data:
            return data
        return _save_battle_cache()

    def __unicode__(self):
        return u'<Battle: %s>' % self.name

    class Meta:
        db_table = 'battle'
        ordering = ('id',)
        verbose_name = "战役"
        verbose_name_plural = "战役"


def _save_battle_cache(*args, **kwargs):
    battles = Battle.objects.all()
    data = {b.id: b for b in battles}
    cache.set('battle', data, hours=None)
    return data

post_save.connect(
    _save_battle_cache,
    sender=Battle,
    dispatch_uid='apps.stage.Battle.post_save'
)

post_delete.connect(
    _save_battle_cache,
    sender=Battle,
    dispatch_uid='apps.stage.Battle.post_delete'
)


class Stage(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField("名字", max_length=32)
    des = models.TextField("描述", blank=True)
    bg = models.CharField("背景图片", max_length=32, blank=True)
    level = models.IntegerField("关卡等级")

    battle = models.ForeignKey(Battle, verbose_name="所属战役")

    open_condition = models.IntegerField("前置关卡ID", null=True, blank=True,
                                         help_text="不填写表示没有前置关卡ID"
                                         )
    monsters = models.TextField("怪物ID")

    normal_exp = models.IntegerField("普通经验")
    normal_gold = models.IntegerField("普通金币")
    normal_drop = models.CharField("普通掉落", max_length=255, blank=True)

    first_exp = models.IntegerField("首通经验")
    first_gold = models.IntegerField("首通金币")
    first_drop = models.CharField("首通掉落", max_length=255, blank=True)

    star_exp = models.IntegerField("三星经验")
    star_gold = models.IntegerField("三星金币")
    star_drop = models.CharField("三星掉落", max_length=255, blank=True)


    def __unicode__(self):
        return u'<Stage: %s>' % self.name

    @staticmethod
    def all():
        data = cache.get('stage', hours=None)
        if data:
            return data
        return _save_stage_cache()

    @property
    def decoded_monsters(self):
        return [int(i) for i in self.monsters.split(',')]


    class Meta:
        db_table = 'stage'
        ordering = ('id',)
        verbose_name = "关卡"
        verbose_name_plural = "关卡"


def _save_stage_cache(*args, **kwargs):
    stages = Stage.objects.all()
    data = {s.id: s for s in stages}
    for _id, s in data.items():
        open_condition = s.open_condition
        if not open_condition:
            continue

        data[open_condition].next = _id

    cache.set('stage', data, hours=None)
    return data


post_save.connect(
    _save_stage_cache,
    sender=Stage,
    dispatch_uid='apps.stage.Stage.post_save'
)

post_delete.connect(
    _save_stage_cache,
    sender=Stage,
    dispatch_uid='apps.stage.Stage.post_delete'
)


class StageDrop(models.Model):
    id = models.IntegerField(primary_key=True)
    drops = models.CharField("物品掉落", max_length=255, help_text="id:prob,id:prob")

    class Meta:
        db_table = 'stagedrop'
        ordering = ('id',)
        verbose_name = "关卡物品掉落"
        verbose_name_plural = "关卡物品掉落"

    @staticmethod
    def all():
        data = cache.get('stagedrop', hours=None)
        if data:
            return data
        return _save_stagedrop_cache()


def _save_stagedrop_cache(*args, **kwargs):
    drops = StageDrop.objects.all()
    data = {d.id: d for d in drops}
    cache.set('stagedrop', data, hours=None)
    return data

post_save.connect(
    _save_stagedrop_cache,
    sender=StageDrop,
    dispatch_uid='apps.stage.StageDrop.post_save'
)

post_delete.connect(
    _save_stagedrop_cache,
    sender=StageDrop,
    dispatch_uid='apps.stage.StageDrop.post_delete'
)




class EliteStage(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField("名字", max_length=32)
    bg = models.CharField("背景图片", max_length=32, blank=True)
    level = models.IntegerField("关卡等级", default=1)

    times = models.IntegerField("次数限制")

    open_condition = models.IntegerField("前置关卡ID", null=True, blank=True,
                                         help_text="不填写表示没有前置关卡ID"
                                         )
    monsters = models.TextField("怪物ID")

    normal_exp = models.IntegerField("经验", default=0)
    normal_gold = models.IntegerField("金币", default=0)
    normal_drop = models.CharField("掉落", max_length=255)


    def __unicode__(self):
        return u'<EliteStage: %s>' % self.name

    @staticmethod
    def all():
        data = cache.get('elitestage', hours=None)
        if data:
            return data
        return _save_elitestage_cache()

    @staticmethod
    def condition_table():
        data = cache.get('elitestage_condition', hours=None)
        if data:
            return data
        _save_elitestage_cache()
        return cache.get('elitestage_condition', hours=None)

    @property
    def decoded_monsters(self):
        return [int(i) for i in self.monsters.split(',')]


    class Meta:
        db_table = 'stage_elite'
        ordering = ('id',)
        verbose_name = "精英关卡"
        verbose_name_plural = "精英关卡"



def _save_elitestage_cache(*args, **kwargs):
    stages = EliteStage.objects.all()
    data = {}
    conditions = {}
    for s in stages:
        data[s.id] = s
        conditions[s.open_condition] = s.id

    cache.set('elitestage', data, hours=None)
    cache.set('elitestage_condition', conditions, hours=None)
    return data


post_save.connect(
    _save_elitestage_cache,
    sender=EliteStage,
    dispatch_uid='apps.stage.EliteStage.post_save'
)

post_delete.connect(
    _save_elitestage_cache,
    sender=EliteStage,
    dispatch_uid='apps.stage.EliteStage.post_delete'
)


class ChallengeStage(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField("名字", max_length=64)
    level = models.IntegerField("档次")
    char_level_needs = models.IntegerField("角色等级需求")
    open_condition_id = models.IntegerField("需要道具ID")
    open_condition_amount = models.IntegerField("需要道具数量")
    power_range = models.CharField("战斗力范围", max_length=64, help_text='min,max')

    aid_limit = models.IntegerField("援军上限")
    time_limit = models.IntegerField("战斗总时间限制", help_text="秒")
    reward_gold = models.IntegerField("奖励金币")

    class Meta:
        db_table = 'stage_challenge'
        ordering = ('id',)
        verbose_name = "猛将挑战"
        verbose_name_plural = "猛将挑战"

    @staticmethod
    def all():
        data = cache.get('challengestage', hours=None)
        if data:
            return data
        return save_challenge_stage_cache()

    def boss_power(self):
        a, b = self.power_range.split(',')
        a, b = int(a), int(b)
        power_range = range(a, b+1)
        return random.choice(power_range)


def save_challenge_stage_cache(*args, **kwargs):
    stages = ChallengeStage.objects.all()
    data = {s.id: s for s in stages}
    cache.set('challengestage', data, hours=None)
    return data


post_save.connect(
    save_challenge_stage_cache,
    sender=ChallengeStage,
    dispatch_uid='apps.stage.ChallengeStage.post_save'
)

post_delete.connect(
    save_challenge_stage_cache,
    sender=ChallengeStage,
    dispatch_uid='apps.stage.ChallengeStage.post_delete'
)

