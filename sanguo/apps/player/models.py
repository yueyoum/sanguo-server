from django.db import models
from django.utils import timezone

class User(models.Model):
    email = models.CharField(max_length=64, blank=True, db_index=True)
    passwd = models.CharField(max_length=40, blank=True)
    device_token = models.CharField(max_length=40, blank=True, db_index=True)

    last_login = models.DateTimeField(default=timezone.now())


    def __unicode__(self):
        return u'<User %d>' % self.id

    @classmethod
    def is_bind(cls, device_token, queryset=None):
        if queryset is None:
            queryset = cls.objects.filter(device_token=device_token)

        for user in queryset:
            if user.email:
                return True

        return False

    class Meta:
        db_table = 'user'

