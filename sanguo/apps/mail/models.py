# -*- coding: utf-8 -*-

from django.db import models
from protomsg import Attachment as MsgAttachment


class Mail(models.Model):
    SEND_TYPE = (
        (1, '角色'),
        (2, '指定服务器'),
        (3, '全部服务器'),
    )

    name = models.CharField("标题", max_length=128)
    content = models.TextField("内容")

    # attachment
    gold = models.PositiveIntegerField("金币", default=0)
    sycee = models.PositiveIntegerField("元宝", default=0)
    exp = models.PositiveIntegerField("等级经验", default=0)
    official_exp = models.PositiveIntegerField("官职经验", default=0)
    heros = models.CharField("武将", max_length=255, blank=True,
                             help_text='id,id,id'
                             )

    equipments = models.CharField("装备", max_length=255, blank=True,
                              help_text='id:amount,id:amount'
                              )
    gems = models.CharField("宝石", max_length=255, blank=True,
                            help_text='id:amount,id:amount'
                            )
    stuffs = models.CharField("材料", max_length=255, blank=True,
                             help_text='id:amount,id:amount'
                             )

    create_at = models.DateTimeField(auto_now_add=True)
    send_at = models.DateTimeField("发送时间", db_index=True)

    send_type = models.IntegerField("发送模式", choices=SEND_TYPE)
    send_to = models.CharField("发送到ID", max_length=255, blank=True,
                               help_text='id,id,id'
                               )

    send_lock = models.BooleanField("正在发送", default=False, db_index=True)
    send_done = models.BooleanField("发送成功", default=False, db_index=True)

    def __unicode__(self):
        return u'<Mail: %s>' % self.name

    class Meta:
        db_table = 'mail'
        verbose_name = '邮件'
        verbose_name_plural = '邮件'

    def to_attachment_protobuf(self):
        msg = MsgAttachment()
        if self.gold:
            msg.gold = self.gold
        if self.sycee:
            msg.sycee = self.sycee
        if self.official_exp:
            msg.official_exp = self.official_exp
        if self.heros:
            msg.heros.extend(self.heros)

        if self.equipments:
            for item in self.equipments.split(','):
                item_id, item_amount = item.split(':')
                e = msg.equipments.add()
                e.id = int(item_id)
                e.level = 1
                e.step = 1
                e.amount = int(item_amount)

        if self.gems:
            for item in self.gems.split(','):
                item_id, item_amount = item.split(':')
                g = msg.gems.add()
                g.id = int(item_id)
                g.amount = int(item_amount)

        if self.stuffs:
            for item in self.stuffs.split(','):
                item_id, item_amount = item.split(':')
                s = msg.stuffs.add()
                s.id = int(item_id)
                s.amount = int(item_amount)

        return msg

