# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/8/14'

from mongoengine import DoesNotExist

from core.mongoscheme import MongoTask

from core.character import Char
from core.attachment import Attachment
from core.achievement import Achievement

from core.msgpipe import publish_to_char
from core.exception import InvalidOperate
from utils import pack_msg

from protomsg import Task as MsgTask
from protomsg import TaskNotify
from protomsg import Attachment as MsgAttachment

from preset.data import TASKS, TASKS_FIRST_IDS, TASKS_ALL_TP


class Task(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.task = MongoTask.objects.get(id=char_id)
        except DoesNotExist:
            self.task = MongoTask(id=char_id)
            for tp in TASKS_ALL_TP:
                self.task.tasks[str(tp)] = 0
            self.task.complete = []
            self.task.finished = []
            self.task.doing = TASKS_FIRST_IDS
            self.task.save()

        self.check()


    def check(self):
        for t in self.task.doing:
            if t in self.task.complete:
                continue

            this_task = TASKS[t]
            tp = this_task.tp

            if self.task.tasks[str(tp)] >= this_task.times:
                # 此任务完成
                if t not in self.task.finished:
                    self.task.finished.append(t)

                attachment = Attachment(self.char_id)
                attachment.save_to_prize(5)

        self.task.save()

    def trig(self, tp, times=1):
        # TODO 检查TP ?

        self.task.tasks[str(tp)] += times

        for t in self.task.doing:
            this_task = TASKS[t]
            if this_task.tp != tp:
                continue

            if self.task.tasks[str(tp)] >= this_task.times:
                # 此任务完成
                if t not in self.task.finished:
                    self.task.finished.append(t)

                attachment = Attachment(self.char_id)
                attachment.save_to_prize(5)


        self.task.save()
        self.send_notify()


    def get_reward(self, _id):
        # FIXME 重复领奖？？？
        try:
            this_task = TASKS[_id]
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
        char.update(sycee=sycee, gold=gold, des="Task {0} Reward".format(_id))

        if this_task.next_task:
            next_task = TASKS[this_task.next_task]
            if self.task.tasks[str(this_task.tp)] >= next_task.times:
                self.task.finished.append(this_task.next_task)

            index = self.task.doing.index(_id)
            self.task.doing.pop(index)
            self.task.doing.insert(index, this_task.next_task)

        self.task.finished.remove(_id)
        self.task.complete.append(_id)
        self.task.save()
        self.send_notify()

        if self.all_complete():
            achievement = Achievement(self.char_id)
            achievement.trig(30, 1)

        msg = MsgAttachment()
        msg.gold = gold
        msg.sycee = sycee
        return msg


    def all_complete(self):
        for tid in self.task.doing:
            this_task = TASKS[tid]
            if this_task.next_task:
                return False

        return True


    def send_notify(self):
        msg = TaskNotify()
        for t in self.task.doing:
            this_task = TASKS[t]
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


