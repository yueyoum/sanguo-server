# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-7-11'

from django.core.management.base import BaseCommand

from core.mongoscheme import MongoTask
from preset.data import TASKS, TASKS_ALL_TP, TASKS_FIRST_IDS


def _expand_task_ids(first_id):
    t = TASKS[first_id]
    ids = [first_id]
    while t.next_task:
        ids.append(t.next_task)
        t = TASKS[t.next_task]

    return ids


class Command(BaseCommand):
    help = """load configs. args:
    task    load new tasks. used when adding new tasks
    """

    def handle(self, *args, **options):
        if not args:
            self.stdout.write(self.help)
            return

        if args[0] == 'task':
            self._cmd_load_task()
        else:
            self.stdout.write(self.help)


    def _cmd_load_task(self):
        def _load_for_one(m):
            """

            :param m:
            :type m: MongoTask
            """
            for tp in TASKS_ALL_TP:
                if str(tp) not in m.tasks:
                    m.tasks[str(tp)] = 0

            for _id in TASKS_FIRST_IDS:
                this_task_ids = _expand_task_ids(_id)
                for _this_id in this_task_ids:
                    if _this_id in m.doing:
                        break
                else:
                    m.doing.append(_id)

            m.doing.sort()
            m.save()

        for m in MongoTask.objects.all():
            _load_for_one(m)
