# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.signals import post_save

from apps.character.cache import save_cache_character

from apps.account.models import Account
from apps.server.models import Server


class Character(models.Model):
    account_id = models.IntegerField("帐号ID")
    server_id = models.IntegerField("服务器ID")

    name = models.CharField("名字", max_length=7, db_index=True)

    gold = models.PositiveIntegerField("金币", default=0)
    sycee = models.PositiveIntegerField("元宝", default=0)

    level = models.PositiveIntegerField("等级", default=1)
    exp = models.PositiveIntegerField("等级经验", default=0)

    official = models.PositiveIntegerField("官职", default=1)
    off_exp = models.PositiveIntegerField("官职经验", default=0)

    # 声望  来自比武日/周奖励， 用于商城购买
    renown = models.PositiveIntegerField("声望", default=0)

    # 积分  来自每场比武奖励， 用于比武排名
    score_day = models.PositiveIntegerField("日积分", default=0)
    score_week = models.PositiveIntegerField("周积分", default=0)


    def update_needs_exp(self, level=None):
        """

        @param level: None or Char level
        @type level: None or int
        @return: the exp which needs for update to next level
        @rtype: int
        """
        level = level or self.level
        exp = pow(level, 2.5) + level * 20
        return int(round(exp * 10, -1))


    def __unicode__(self):
        return u'<Character %d:%d:%d, %s>' % (
            self.account_id, self.server_id, self.id, self.name
        )

    class Meta:
        db_table = 'char_'
        unique_together = (
            ('account_id', 'server_id'),
            ('server_id', 'name'),
        )
        verbose_name = "角色"
        verbose_name_plural = "角色"


def character_save_callback(sender, instance, **kwargs):
    # character其他数据直接在外部初始化完了。这里不用hook
    save_cache_character(instance)


post_save.connect(
    character_save_callback,
    sender=Character,
    dispatch_uid='apps.character.Character.post_save'
)

