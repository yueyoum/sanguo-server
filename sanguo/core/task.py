# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/8/14'

from mongoengine import DoesNotExist

from core.mongoscheme import MongoTask
from apps.task.models import Task as ModelTask

from core.character import Char

from core.msgpipe import publish_to_char
from core.exception import InvalidOperate
from utils import pack_msg

from protomsg import Task as MsgTask
from protomsg import TaskNotify

class Task(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.task = MongoTask.objects.get(id=char_id)
        except DoesNotExist:
            self.task = MongoTask(id=char_id)
            all_task_tps = ModelTask.all_tp()
            for tp in all_task_tps:
                self.task.tasks[str(tp)] = 0
            self.task.complete = []
            self.task.finished = []
            self.task.doing = ModelTask.first_ids()
            self.task.save()

        self.check()


    def check(self):
        all_tasks = ModelTask.all()
        for t in self.task.doing:
            this_task = all_tasks[t]
            tp = this_task.tp

            if self.task.tasks[str(tp)] >= this_task.times:
                # 此任务完成
                if t not in self.task.finished:
                    self.task.finished.append(t)

        self.task.save()

    def trig(self, tp, times=1):
        # TODO 检查TP ?

        self.task.tasks[str(tp)] += times
        all_tasks = ModelTask.all()

        for t in self.task.doing:
            this_task = all_tasks[t]
            if this_task.tp != tp:
                continue

            if self.task.tasks[str(tp)] >= this_task.times:
                # 此任务完成
                if t not in self.task.finished:
                    self.task.finished.append(t)

        self.task.save()
        self.send_notify()


    def get_reward(self, _id):
        all_tasks = ModelTask.all()
        try:
            this_task = all_tasks[_id]
        except KeyError:
            raise InvalidOperate("Task Get Reward: Char {0} Try to get reward from a NONE exist task {1}".format(
                self.char_id, _id
            ))

        if _id not in self.task.finished:
            raise InvalidOperate("Task Get Reward: Char {0} Try to get reward from task {1}. But this task not FINISHED".format(
                self.char_id, _id
            ))

        char = Char(self.char_id)
        sycee = this_task.sycee if this_task.sycee else 0
        gold = this_task.gold if this_task.gold else 0
        char.update(sycee=sycee, gold=gold)

        if this_task.next_task:
            next_task = all_tasks[this_task.next_task]
            if self.task.tasks[str(this_task.tp)] >= next_task.times:
                self.task.finished.append(this_task.next_task)

            index = self.task.doing.index(_id)
            self.task.doing.pop(index)
            self.task.doing.insert(index, this_task.next_task)

        self.task.finished.remove(_id)
        self.task.complete.append(_id)
        self.task.save()
        self.send_notify()



    def send_notify(self):
        msg = TaskNotify()
        all_tasks = ModelTask.all()
        for t in self.task.doing:
            this_task = all_tasks[t]
            msg_t = msg.tasks.add()
            msg_t.id = t
            msg_t.current_times = self.task.tasks[str(this_task.tp)]

            if t in self.task.complete:
                status = MsgTask.COMPLETE
            elif t in self.task.finished:
                status = MsgTask.REWARD
            else:
                status = MsgTask.DOING

            msg_t.status = status

        publish_to_char(self.char_id, pack_msg(msg))


