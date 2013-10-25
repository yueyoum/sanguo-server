from django.db import models
from django.utils import timezone

class Server(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=16)
    max_player_count = models.IntegerField()

    active = models.BooleanField(default=True)
    create_time = models.DateTimeField()

    def __unicode__(self):
        return u'<Server %d>' % self.id

    def save(self, *args, **kwargs):
        if not self.create_time:
            self.create_time = timezone.now()
        super(Server, self).save(*args, **kwargs)

    class Meta:
        db_table = 'sanguo_server'

