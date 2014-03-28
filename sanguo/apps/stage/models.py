# -*- coding: utf-8 -*-

from django.db import models


class Battle(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField("名字", max_length=32)
    level_limit = models.IntegerField("等级限制", default=1)
    des = models.TextField("描述", blank=True)

    def __unicode__(self):
        return u'<Battle: %s>' % self.name

    class Meta:
        db_table = 'battle'
        ordering = ('id',)
        verbose_name = "战役"
        verbose_name_plural = "战役"



class Stage(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField("名字", max_length=32)

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


    class Meta:
        db_table = 'stage'
        ordering = ('id',)
        verbose_name = "关卡"
        verbose_name_plural = "关卡"


class StageDrop(models.Model):
    id = models.IntegerField(primary_key=True)
    equips = models.CharField("装备掉落", max_length=255, blank=True, help_text="id:prob,id:prob")
    gems = models.CharField("宝石掉落", max_length=255, blank=True, help_text='id:prob,id:prob')
    stuffs = models.CharField("材料掉落", max_length=255, blank=True, help_text='id:prob,id:prob')

    class Meta:
        db_table = 'stagedrop'
        ordering = ('id',)
        verbose_name = "关卡物品掉落"
        verbose_name_plural = "关卡物品掉落"



class EliteStage(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField("名字", max_length=32)
    bg = models.CharField("背景图片", max_length=32, blank=True)
    level = models.IntegerField("关卡等级", default=1)

    times = models.IntegerField("次数限制")

    open_condition = models.IntegerField("前置关卡ID")
    monsters = models.TextField("怪物ID")

    normal_exp = models.IntegerField("经验", default=0)
    normal_gold = models.IntegerField("金币", default=0)
    normal_drop = models.CharField("掉落", max_length=255, blank=True)


    def __unicode__(self):
        return u'<EliteStage: %s>' % self.name


    class Meta:
        db_table = 'stage_elite'
        ordering = ('id',)
        verbose_name = "精英关卡"
        verbose_name_plural = "精英关卡"



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


