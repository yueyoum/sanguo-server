# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.signals import post_save

from utils import cache

def level_update_exp(level):
    exp = pow(level, 2.5) + level * 20
    return int(round(exp * 10, -1))


def official_update_exp(level):
    exp = pow(level + 1, 3.2) * 0.2 + (level + 1) * 20
    return int(round(exp, -1))


class Character(models.Model):
    account_id = models.IntegerField("帐号ID")
    server_id = models.IntegerField("服务器ID")

    name = models.CharField("名字", max_length=7, db_index=True)

    gold = models.PositiveIntegerField("金币", default=0)
    sycee = models.PositiveIntegerField("元宝", default=0)

    level = models.PositiveIntegerField("等级", default=1, db_index=True)
    exp = models.PositiveIntegerField("等级经验", default=0)

    official = models.PositiveIntegerField("官职", default=0)
    off_exp = models.PositiveIntegerField("官职经验", default=0)


    @staticmethod
    def cache_obj(_id):
        c = cache.get('char:{0}'.format(_id))
        if c:
            return c

        try:
            obj = Character.objects.get(id=_id)
            return _save_cache_character(obj)
        except Character.DoesNotExist:
            return None



    def update_needs_exp(self, level=None):
        level = level or self.level
        return level_update_exp(level)


    def update_official_needs_exp(self, level=None):
        level = level or self.official
        return official_update_exp(level)


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



def _save_cache_character(obj):
    cache.set('char:{0}'.format(obj.id), obj)
    return obj

def character_save_callback(instance, **kwargs):
    # character其他数据直接在外部初始化完了。这里不用hook
    _save_cache_character(instance)


post_save.connect(
    character_save_callback,
    sender=Character,
    dispatch_uid='apps.character.Character.post_save'
)


class CharPropertyLog(models.Model):
    char_id = models.IntegerField(db_index=True)
    gold = models.IntegerField("金币", default=0)
    sycee = models.IntegerField("元宝", default=0)
    exp = models.IntegerField("经验", default=0)
    official_exp = models.IntegerField("官职经验", default=0)
    des = models.CharField("描述", max_length=255, blank=True)
    add_time = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'char_log'
        ordering = ('-add_time',)
        verbose_name = '角色日志'
        verbose_name_plural = '角色日志'

