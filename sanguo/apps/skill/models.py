# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.signals import post_delete, post_save

from utils import cache

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

    def __unicode__(self):
        return u'<Skill %s>' % self.name

    @staticmethod
    def cache_obj(sid):
        data = Skill.all()
        return data[sid]

    @staticmethod
    def all():
        data = cache.get('skill', hours=None)
        if data:
            return data
        return _save_cache_skill()

    @staticmethod
    def update_cache():
        return _save_cache_skill()


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


class UsingEffect(object):
    __slots__ = ['id', 'target', 'value', 'rounds']
    def __init__(self, id, target, value, rounds):
        self.id = id
        self.target = target
        self.value = value
        self.rounds =  rounds

    def copy(self):
        return UsingEffect(self.id, self.target, self.value, self.rounds)


def _save_cache_skill(*args, **kwargs):
    skills = Skill.objects.all()
    data = {}
    for s in skills:
        effects = s.skilleffect_set.all()
        using_effects = []
        for e in effects:
            using_effects.append(
                UsingEffect(e.effect_id, e.target, e.value, e.rounds)
            )

        s.effects = using_effects
        data[s.id] = s

    cache.set('skill', data, hours=None)
    return data


post_save.connect(_save_cache_skill, sender=Effect)
post_save.connect(_save_cache_skill, sender=Skill)
post_save.connect(_save_cache_skill, sender=SkillEffect)

post_delete.connect(_save_cache_skill, sender=Effect)
post_delete.connect(_save_cache_skill, sender=Skill)
post_delete.connect(_save_cache_skill, sender=SkillEffect)

