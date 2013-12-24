# -*- coding: utf-8 -*-

from django.db import models
from django.utils import timezone

class User(models.Model):
    email = models.CharField(max_length=64, blank=True, db_index=True)
    passwd = models.CharField(max_length=40, blank=True)
    device_token = models.CharField(max_length=40, blank=True, db_index=True)

    register_at = models.DateTimeField()
    last_login = models.DateTimeField()
    last_server_id = models.IntegerField(default=0)
    login_times = models.PositiveIntegerField()
    
    # TODO 登录平台
    platform = models.CharField(max_length=32, blank=True)
    
    active = models.BooleanField(default=True)


    def __unicode__(self):
        return u'<User %d>' % self.id
    
    def save(self, *args, **kwargs):
        if not self.register_at:
            self.register_at = timezone.now()

        self.last_login = timezone.now()
        if not self.login_times:
            self.login_times = 1
        else:
            self.login_times += 1
        
        if not self.platform:
            self.platform = 'unknown'
        
        self.platform = self.platform[:32]
        super(User, self).save(*args, **kwargs)

    class Meta:
        db_table = 'user'

