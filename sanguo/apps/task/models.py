# -*- coding:utf-8 -*-

from django.db import models
from django.db.models.signals import post_delete, post_save

from utils import cache

class Task(models.Model):
    id = models.IntegerField(primary_key=True)
    tp = models.IntegerField("类型")
    name = models.CharField("名字", max_length=32)
    times = models.IntegerField("次数")
    sycee = models.IntegerField("奖励元宝", null=True, blank=True)
    gold = models.IntegerField("奖励金币", null=True, blank=True)
    next_task = models.IntegerField("下一档任务ID", null=True, blank=True)

    class Meta:
        db_table = 'task'
        ordering = ('id',)
        verbose_name = "日常任务"
        verbose_name_plural = "日常任务"

    @staticmethod
    def all():
        data = cache.get('task', hours=None)
        if data:
            return data
        return save_task_cache()



def save_task_cache(*args, **kwargs):
    tasks = Task.objects.all()
    data = {t.id: t for t in tasks}
    cache.set('task', data, hours=None)
    return data

post_save.connect(
    save_task_cache,
    sender=Task,
    dispatch_uid='apps.task.Task.post_save'
)

post_delete.connect(
    save_task_cache,
    sender=Task,
    dispatch_uid='apps.task.Task.post_delete'
)

