# -*- coding: utf-8 -*-

from django.db import models


# 角色初始化
class CharInit(models.Model):
    gold = models.IntegerField("金币", default=0)
    sycee = models.IntegerField("元宝", default=0)

    heros = models.CharField("武将", max_length=255, help_text="武将:武器,防具,饰品|武将:武器,防具,饰品")
    gems = models.CharField("宝石", max_length=255, help_text="id:amount,id:amount,id:amount")
    stuffs = models.CharField("杂物", max_length=255, help_text="id:amount,id:amount,id:amount")

    class Meta:
        db_table = 'config_charinit'
        verbose_name = "角色初始化"
        verbose_name_plural = "角色初始化"


# 比武排名奖励
class ArenaReward(models.Model):
    id = models.IntegerField("排名级别", primary_key=True)
    name = models.CharField("称谓", max_length=32, blank=True)
    day_gold = models.IntegerField("日金币")
    week_gold = models.IntegerField("周金币")
    week_stuffs = models.CharField("周材料", max_length=255, blank=True)

    class Meta:
        db_table = 'arena_reward'
        verbose_name = "比武奖励"
        verbose_name_plural = "比武奖励"
        ordering = ('id',)


# 通知消息模板
class Notify(models.Model):
    id = models.IntegerField(primary_key=True)
    template = models.CharField("模板", max_length=255)
    des = models.CharField("说明", max_length=255, blank=True)

    class Meta:
        db_table = 'notify'
        ordering = ('id',)
        verbose_name = '消息模板'
        verbose_name_plural = '消息模板'


# 功能开放
class FunctionOpen(models.Model):
    FUNC_ID = (
        (1, '装备强化'),
        (2, '装备进阶'),
        (3, '武将进阶'),
        (4, '宝石镶嵌'),
        (5, '日常任务'),
        (6, '成就任务'),
        (7, '挂机功能'),
        (8, '比武功能'),
        (9, '掠夺功能'),
        (10, '官职功能'),
        (11, '精英副本'),
        (12, '好友功能'),
        (13, '猛将挑战'),
    )

    SOCKET_AMOUNT = (
        (4, '上阵四人'),
        (5, '上阵五人'),
        (6, '上阵六人'),
        (7, '上阵七人'),
        (8, '上阵八人'),
    )

    char_level = models.IntegerField("君主等级条件", default=0)
    stage_id = models.IntegerField("关卡ID条件", default=0)

    func_id = models.IntegerField("开启功能", choices=FUNC_ID, null=True, blank=True)
    socket_amount = models.IntegerField("上阵人数", choices=SOCKET_AMOUNT, null=True, blank=True)

    class Meta:
        db_table = 'function_open'
        ordering = ('id',)
        verbose_name = '功能开启'
        verbose_name_plural = '功能开启'



# 对话
class Dialog(models.Model):
    START_AT = (
        (1, '开始'),
        (2, '结束'),
    )
    stage_id = models.IntegerField("关卡ID")
    ground_id = models.IntegerField("哪一军")
    start_at = models.IntegerField("开始于", choices=START_AT)

    class Meta:
        db_table = 'dialog'
        ordering = ('id',)
        verbose_name = "对话"
        verbose_name_plural = "对话"


class DialogStatement(models.Model):
    POSITION = (
        (1, '左'),
        (2, '右'),
    )

    dialog = models.ForeignKey(Dialog)
    position = models.IntegerField("位置", choices=POSITION)
    who = models.IntegerField("武将ID")
    speech = models.CharField("发言", max_length=255)

    class Meta:
        db_table = 'dialog_statement'
        ordering = ('id',)

# 新手引导
class GameGuide(models.Model):
    SHAPE = (
        (1, '圆形'),
        (2, '方形'),
    )

    guide_id = models.IntegerField()
    speech = models.CharField("发言", max_length=255, blank=True)
    area_x = models.IntegerField(default=0)
    area_y = models.IntegerField(default=0)
    area_shape = models.IntegerField(choices=SHAPE)
    area_size = models.CharField("尺寸", max_length=255)

    class Meta:
        db_table = 'game_guide'
        ordering = ('id',)
        verbose_name = '新手引导'
        verbose_name_plural = '新手引导'
