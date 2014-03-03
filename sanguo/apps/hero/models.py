# -*- coding: utf-8 -*-
import random
from django.db import models
from django.db.models.signals import post_delete, post_save
from utils import cache

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

    def __unicode__(self):
        return u'<Hero: %s>' % self.name

    @staticmethod
    def all():
        data = cache.get('hero', hours=None)
        if data:
            return data
        return _save_cache_hero()

    @staticmethod
    def get_by_quality(quality, amount=1):
        assert quality in [1, 2, 3]

        all_heros = Hero.all()
        all_heros_items = all_heros.items()
        res = {}
        while True:
            if len(res) >= amount:
                break
            this = random.choice(all_heros_items)
            if this[0] in res:
                continue
            if this[1].quality != quality:
                continue

            res[this[0]] = this[1]

        return res


    @staticmethod
    def get_by_quality_not_equal(quality, amount=1):
        assert quality in [1, 2, 3]

        all_heros_items = Hero.all().items()
        res = {}
        while True:
            if len(res) >= amount:
                break

            this = random.choice(all_heros_items)
            if this[0] in res:
                continue
            if this[1].quality == quality:
                continue

            res[this[0]] = this[1]

        return res

    @staticmethod
    def get_by_grade(grade, amount=1):

        all_heros = Hero.all()
        all_heros_items = all_heros.items()
        res = {}
        while True:
            if len(res) >= amount:
                break
            this = random.choice(all_heros_items)
            if this[0] in res:
                continue
            if this[1].grade != grade:
                continue

            res[this[0]] = this[1]

        return res


    @staticmethod
    def update_cache():
        return _save_cache_hero()


    def special_equipments(self):
        data = getattr(self, '_special_equipments', None)
        if data:
            return data

        if not self.special_equip_cls:
            return {}
        equip_cls = [int(i) for i in self.special_equip_cls.split(',')]
        equip_addition = [int(i) for i in self.special_addition.split(',')]
        data = dict(zip(equip_cls, equip_addition))
        self._special_equipments = data
        return data


    class Meta:
        db_table = 'hero'
        ordering = ('id',)
        verbose_name = "武将"
        verbose_name_plural = "武将"


def _save_cache_hero():
    heros = Hero.objects.all()
    data = {h.id: h for h in heros}
    cache.set('hero', data, hours=None)
    return data


def _update_hero_cache(*args, **kwargs):
    _save_cache_hero()


post_save.connect(
    _update_hero_cache,
    sender=Hero,
    dispatch_uid='apps.hero.Hero.post_save'
)

post_delete.connect(
    _update_hero_cache,
    sender=Hero,
    dispatch_uid='apps.hero.Hero.post_delete'
)


class Monster(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField("名字", max_length=16)
    avatar = models.CharField("头像", max_length=32)
    image = models.CharField("卡牌", max_length=32)

    level = models.IntegerField("等级")
    attack = models.IntegerField("攻击")
    defense = models.IntegerField("防御")
    hp = models.IntegerField("生命")
    crit = models.IntegerField("暴击", default=0)
    dodge = models.IntegerField("闪避", default=0)

    skills = models.CharField("技能", blank=True, max_length=255)

    def __unicode__(self):
        return u'<Monster: %s>' % self.name

    @staticmethod
    def all():
        data = cache.get('monster', hours=None)
        if data:
            return data
        return _save_cache_monster()

    @staticmethod
    def update_cache():
        return _save_cache_monster()

    class Meta:
        db_table = 'monster'
        ordering = ('id',)
        verbose_name = "怪物"
        verbose_name_plural = "怪物"


def _save_cache_monster():
    monsters = Monster.objects.all()
    data = {m.id: m for m in monsters}
    cache.set('monster', data, hours=None)
    return data

def _update_monster_cache(*args, **kwargs):
    _save_cache_monster()


post_save.connect(
    _update_monster_cache,
    sender=Monster,
    dispatch_uid='apps.hero.Monster.post_save'
)

post_delete.connect(
    _update_monster_cache,
    sender=Monster,
    dispatch_uid='apps.hero.Monster.post_delete'
)

