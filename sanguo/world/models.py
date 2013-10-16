from django.db import models

class Server(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=16)
    max_player_count = models.IntegerField()

    def __unicode__(self):
        return u'<Server %d>' % self.id


