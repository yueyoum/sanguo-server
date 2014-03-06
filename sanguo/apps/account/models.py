# -*- coding: utf-8 -*-

from django.db import models
from django.utils import timezone


class Account(models.Model):
    email = models.CharField("EMAIL", max_length=64, blank=True, db_index=True, editable=False)
    passwd = models.CharField("密码", max_length=40, blank=True)
    device_token = models.CharField("设备码", max_length=40, blank=True, db_index=True)

    register_at = models.DateTimeField("注册于")
    last_login = models.DateTimeField("最后登录", db_index=True)
    last_server_id = models.IntegerField("最后服务器ID", default=0)
    all_server_ids = models.CharField("登录过的所有服务器ID", default='', max_length=255)
    login_times = models.PositiveIntegerField("登录次数")

    active = models.BooleanField("激活", default=True)


    def __unicode__(self):
        return u'<Account %d>' % self.id

    def save(self, *args, **kwargs):
        if not self.register_at:
            self.register_at = timezone.now()

        self.last_login = timezone.now()
        if not self.login_times:
            self.login_times = 1
        else:
            self.login_times += 1

        if len(self.all_server_ids) < 253:
            all_server_ids = self.all_server_ids.split(',')
            if self.last_server_id and str(self.last_server_id) not in all_server_ids:
                all_server_ids.append(str(self.last_server_id))
                self.all_server_ids = ','.join(all_server_ids)

        super(Account, self).save(*args, **kwargs)

    class Meta:
        db_table = 'account'
        verbose_name = "帐号"
        verbose_name_plural = "帐号"

