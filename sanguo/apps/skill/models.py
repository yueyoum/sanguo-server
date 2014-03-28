# -*- coding: utf-8 -*-

from django.db import models


class Effect(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField("名字", max_length=32, blank=True)
    des = models.CharField("说明", max_length=32, blank=True)
    buff_icon = models.CharField("Buff图标", max_length=32, blank=True)
    special = models.CharField("特效", max_length=32, blank=True)

    def __unicode__(self):
        return u'<Effect: %s, %s>' % (self.name, self.des)

    class Meta:
        db_table = 'effect'
        ordering = ('id',)
        verbose_name = "技能效果"
        verbose_name_plural = "技能效果"


class Skill(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField("名字", max_length=32)
    des = models.TextField("描述", blank=True)
    cast_effect = models.CharField("施放特效", max_length=32, blank=True)
    hit_effect = models.CharField("命中特效", max_length=32, blank=True)
    is_fullscreen = models.BooleanField("是否全屏", default=False)

    mode = models.IntegerField("类型")
    mode_name = models.CharField("类型名字", max_length=8)

    prob = models.IntegerField("触发几率")
    trig_start = models.IntegerField("触发回合初始", default=1)
    trig_cooldown = models.IntegerField("触发回合间隔")

    anger_self = models.IntegerField("对自己的怒气", default=0)
    anger_self_team = models.IntegerField("对己方的怒气", default=0)
    anger_rival_team = models.IntegerField("对敌方的怒气", default=0)


    def __unicode__(self):
        return u'<Skill %s>' % self.name

    class Meta:
        db_table = 'skill'
        ordering = ('id',)
        verbose_name = "技能"
        verbose_name_plural = "技能"


class SkillEffect(models.Model):
    TARGET = (
        (1, '敌单体'), (2, '自身'),
        (3, '敌全体'), (4, '已全体'),
        (5, '随机敌方一个'), (6, '随机敌方两个'),
        (7, '随机己方一个'), (8, '随机己方两个'),
    )

    skill = models.ForeignKey(Skill)
    effect = models.ForeignKey(Effect, verbose_name="效果")
    target = models.IntegerField("目标", choices=TARGET)
    value = models.IntegerField("数值")
    rounds = models.IntegerField("作用回合")

    class Meta:
        db_table = 'skill_effect'

