from django.db import models

class Character(models.Model):
    account_id = models.IntegerField(db_index=True)
    server_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=10)
    gold = models.IntegerField(default=0)
    gem = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    exp = models.IntegerField(default=0)

    def __unicode__(self):
        return u'<Character %d>' % self.id

    class Meta:
        unique_together = (
                ('account_id', 'server_id'),
                ('server_id', 'name'),
                )

