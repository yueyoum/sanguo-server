from django.db import models
from django.db.models import Max
from django.conf import settings

from core.drives import redis_client

class Character(models.Model):
    account_id = models.IntegerField(db_index=True)
    server_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=10)
    gold = models.IntegerField(default=0)
    gem = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    honor = models.IntegerField(default=0)

    def __unicode__(self):
        return u'<Character %d>' % self.id

    class Meta:
        unique_together = (
                ('account_id', 'server_id'),
                ('server_id', 'name'),
                )


class CharHero(models.Model):
    char = models.ForeignKey(Character, related_name='char_heros')
    hero_id = models.IntegerField()
    level = models.IntegerField(default=1)
    exp = models.IntegerField(default=0)

    def __unicode__(self):
        return u'<CharHero %d %d:%d>' % (self.id, self.char_id, self.hero_id)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = redis_client.incr('charhero_id')
        super(CharHero, self).save(*args, **kwargs)

    @classmethod
    def multi_create(cls, items):
        length = len(items)
        new_max_id = redis_client.incrby('charhero_id', length)

        for index, i in enumerate(range(new_max_id-length+1, new_max_id+1)):
            items[index].id = i

        objs = cls.objects.bulk_create(items)
        return objs


def _save_charhero_max_id_in_redis():
    max_id = CharHero.objects.aggregate(Max('id'))['id__max']
    if max_id is None:
        max_id = 100
    redis_client.set('charhero_id', max_id)

if not settings.TESTING:
    _save_charhero_max_id_in_redis()


