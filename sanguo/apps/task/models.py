# -*- coding:utf-8 -*-

from django.db import models
from django.db.models.signals import post_delete, post_save

from utils import cache

class Task(models.Model):
    id = models.IntegerField(primary_key=True)
    tp = models.IntegerField("类型")
    name = models.CharField("名字", max_length=32)
    first = models.BooleanField("初始任务", default=False)
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
        data = cache.get('task')
        if data:
            return data
        return save_task_cache()

    @staticmethod
    def all_tp():
        data = Task.all()
        tps = []
        for k, v in data.iteritems():
            if v.tp not in tps:
                tps.append(v.tp)
        return tps

    @staticmethod
    def get_by_tp(tp, data=None):
        if not data:
            data = Task.all()
        res = {}
        for k, v in data.iteritems():
            if v.tp == tp:
                res[k] = v
        return res

    @staticmethod
    def first_ids():
        data = Task.all()
        res = []
        for k, v in data.iteritems():
            if v.first:
                res.append(k)
        return res



def save_task_cache(*args, **kwargs):
    tasks = Task.objects.all()
    data = {t.id: t for t in tasks}
    cache.set('task', data, expire=None)
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

