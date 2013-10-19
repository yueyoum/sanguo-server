from django.db import models
from django.utils import timezone

class User(models.Model):
    email = models.CharField(max_length=64, blank=True, db_index=True)
    passwd = models.CharField(max_length=40, blank=True)
    device_token = models.CharField(max_length=40, blank=True, db_index=True)

    last_login = models.DateTimeField(default=timezone.now())

    
    def is_bind(self):
        return True if self.email else False


    def __unicode__(self):
        return u'<User %d>' % self.id


