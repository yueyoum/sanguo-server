# -*- coding:utf-8 -*-
from random import choice

from django.db import models
# from django.db.models.signals import post_delete
# from django.dispatch import receiver

 
class Quality(models.Model):
    attack_base = models.IntegerField()
    defense_base = models.IntegerField()
    hp_base = models.IntegerField()

    def __unicode__(self):
        return self.name



class Hero(models.Model):
    quality_id = models.IntegerField()

    gem_worth = models.IntegerField(blank=True, null=True)
    gold_worth = models.IntegerField(blank=True, null=True)

    attack_grow = models.IntegerField()
    defense_grow = models.IntegerField()
    hp_grow = models.IntegerField()

    crit = models.IntegerField()
    dodge = models.IntegerField()

    skills = models.CharField(max_length=128, blank=True)

    def __unicode__(self):
        return self.name

    @classmethod
    def random_items(cls, nums):
        max_id = cls.objects.aggregate(models.Max('id'))['id__max']
        id_range = range(1, max_id+1)

        i = 0
        while i < nums:
            this_id = choice(id_range)
            id_range.remove(this_id)

            try:
                yield cls.objects.get(id=this_id)
                i += 1
            except cls.DoesNotExist:
                pass

