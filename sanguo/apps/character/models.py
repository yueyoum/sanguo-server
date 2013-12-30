# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.signals import post_save

from apps.character.cache import save_cache_character


class Character(models.Model):
    account_id = models.IntegerField(db_index=True)
    server_id = models.IntegerField(db_index=True)

    name = models.CharField(max_length=10)

    # 金币
    gold = models.PositiveIntegerField(default=0)
    # 元宝
    sycee = models.PositiveIntegerField(default=0)

    # 等级
    level = models.PositiveIntegerField(default=1)
    # 等级经验 这里存的是总经验
    exp = models.PositiveIntegerField(default=0)

    # 官职
    official = models.PositiveIntegerField(default=1)
    # 官职经验，荣誉
    honor = models.PositiveIntegerField(default=0)

    # 声望  来自比武日/周奖励， 用于商城购买
    renown = models.PositiveIntegerField(default=0)

    # 积分  来自每场比武奖励， 用于比武排名
    score_day = models.PositiveIntegerField(default=0)
    score_week = models.PositiveIntegerField(default=0)


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


def character_save_callback(sender, instance, **kwargs):
    # character其他数据直接在外部初始化完了。这里不用hook
    save_cache_character(instance)


post_save.connect(
    character_save_callback,
    sender=Character,
    dispatch_uid='apps.character.Character.post_save'
)

