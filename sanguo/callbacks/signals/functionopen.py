# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-27'

from core.signals import func_opened_signal

from preset.data import TASKS
from core.task import Task
from core.functionopen import FUNCTIONS


def _func_opened(char_id, func_ids, **kwargs):
    need_task_notify = False
    task_related_func_ids = [t.func for t in TASKS.values() if t.func]
    for _id in func_ids:
        if _id in task_related_func_ids:
            need_task_notify = True
            break

    if need_task_notify:
        Task(char_id).send_notify()

    for _id in func_ids:
        Func = FUNCTIONS.get(_id, None)
        if Func:
            Func(char_id).send_notify()

func_opened_signal.connect(
    _func_opened,
    dispatch_uid='callbacks.signals.functionopen._func_opened'
)

