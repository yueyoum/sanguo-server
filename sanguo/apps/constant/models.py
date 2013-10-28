from django.db import models

 
class Quality(models.Model):
    attack_base = models.IntegerField()
    defense_base = models.IntegerField()
    hp_base = models.IntegerField()

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'c_hero_quality'



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
        return u'<Hero %d>' % self.id

    class Meta:
        db_table = 'c_hero'


class GetHero(models.Model):
    mode = models.IntegerField()
    gem = models.IntegerField()
    quality_and_prob = models.TextField()

    class Meta:
        db_table = 'c_get_hero'

