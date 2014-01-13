# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.signals import post_save, post_delete

from worker import tasks

class Mail(models.Model):
    SEND_TYPE = (
        (1, '角色'),
        (2, '服务器'),
        (3, '全部服务器'),
    )

    name = models.CharField("标题", max_length=128)
    content = models.TextField("内容")

    # attachment
    gold = models.PositiveIntegerField("金币", default=0)
    sycee = models.PositiveIntegerField("元宝", default=0)
    exp = models.PositiveIntegerField("等级经验", default=0)
    off_exp = models.PositiveIntegerField("官职经验", default=0)
    renown = models.PositiveIntegerField("声望", default=0)

    equips = models.CharField("装备", max_length=255, blank=True,
                              help_text='id:amount,id:amount'
                              )
    gems = models.CharField("宝石", max_length=255, blank=True,
                            help_text='id:amount,id:amount'
                            )
    props = models.CharField("道具", max_length=255, blank=True,
                             help_text='id:amount,id:amount'
                             )

    create_at = models.DateTimeField(auto_now_add=True)
    send_at = models.DateTimeField("发送时间")

    send_type = models.IntegerField("发送模式", choices=SEND_TYPE)
    send_to = models.CharField("发送到ID", max_length=255, blank=True,
                               help_text='id,id,id'
                               )

    expired = models.BooleanField("失效", default=False)

    def __unicode__(self):
        return u'<Mail: %s>' % self.name

    class Meta:
        db_table = 'mail'
        unique_together = (('expired', 'send_to'),)
        verbose_name = '邮件'
        verbose_name_plural = '邮件'


def _send_mail(instance, created, **kwargs):
    if not created:
        print "NOT CREATED"
        return

    # TODO
    print "CREATED"

    # tasks.send_mail.apply_async((instance.id, instance.send_type, instance.send_to))

def _delete_mail(instance, **kwargs):
    # TODO
    print "DELETE"
    pass

post_save.connect(
    _send_mail,
    sender=Mail,
    dispatch_uid='apps.mail.post_save'
)

post_delete.connect(
    _delete_mail,
    sender=Mail,
    dispatch_uid='apps.mail.post_delete'
)
