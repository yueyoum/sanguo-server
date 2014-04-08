# -*- coding: utf-8 -*-
from django.db import models


class Hero(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField("名字", max_length=16)
    avatar = models.CharField("头像", max_length=32)
    image = models.CharField("卡牌", max_length=32)

    tp = models.IntegerField("类型")
    tp_name = models.CharField("类型名字", max_length=32)

    country = models.IntegerField("国家")
    country_name = models.CharField("国家名字", max_length=32)

    gender = models.IntegerField("性别")
    gender_name = models.CharField("性别名字", max_length=4)

    special_equip_cls = models.CharField("专属装备类别", max_length=255, blank=True,
                                         help_text='ID,ID,ID   没有某项用0代替，都没有不填')
    special_addition = models.CharField("专属加成", max_length=255, blank=True,
                                        help_text='加成,加成,加成   没有某项用0代替，都没有不填'
                                        )

    quality = models.IntegerField("品质")
    quality_name = models.CharField("品质名字", max_length=4)

    grade = models.IntegerField("档次")

    contribution = models.IntegerField("贡献值")

    attack_growing = models.FloatField("攻击成长")
    defense_growing = models.FloatField("防御成长")
    hp_growing = models.FloatField("生命成长")

    crit = models.IntegerField("暴击", default=0)
    dodge = models.IntegerField("闪避", default=0)

    skills = models.CharField("技能", blank=True, max_length=255)
    default_skill = models.IntegerField("默认技能", default=0)

    anger = models.IntegerField("怒气", default=50)

    def __unicode__(self):
        return u'<Hero: %s>' % self.name


    class Meta:
        db_table = 'hero'
        ordering = ('id',)
        verbose_name = "武将"
        verbose_name_plural = "武将"



class Monster(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField("名字", max_length=16)
    image = models.CharField("卡牌", max_length=32)

    tp = models.IntegerField("类型")
    tp_name = models.CharField("类型名字", max_length=32)

    quality = models.IntegerField("品质")
    attack = models.FloatField("攻击成长")
    defense = models.FloatField("防御成长")
    hp = models.FloatField("生命成长")

    crit = models.IntegerField("暴击", default=0)
    dodge = models.IntegerField("闪避", default=0)

    skills = models.CharField("技能", blank=True, max_length=255)
    default_skill = models.IntegerField("默认技能", default=0)

    anger = models.IntegerField("怒气", default=50)

    def __unicode__(self):
        return u'<Monster: %s>' % self.name

    class Meta:
        db_table = 'monster'
        ordering = ('id',)
        verbose_name = "怪物"
        verbose_name_plural = "怪物"

