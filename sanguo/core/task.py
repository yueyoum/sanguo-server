# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/8/14'

from mongoengine import DoesNotExist

from core.mongoscheme import MongoTask

from core.attachment import Attachment, standard_drop_to_attachment_protomsg
from core.achievement import Achievement

from core.msgpipe import publish_to_char
from core.exception import SanguoException
from core.resource import Resource
from utils import pack_msg
from utils.log import system_logger
from utils.checkers import func_opened

from protomsg import Task as MsgTask
from protomsg import TaskNotify

from preset.data import TASKS, TASKS_FIRST_IDS, TASKS_ALL_TP
from preset import errormsg


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
        attachment = Attachment(self.char_id)

        for t in self.task.doing:
            if t in self.task.complete:
                continue

            this_task = TASKS[t]
            tp = this_task.tp

            if self.task.tasks[str(tp)] >= this_task.times:
                # 此任务完成
                if t not in self.task.finished:
                    self.task.finished.append(t)

                attachment.save_to_prize(5)

        self.task.save()

        # XXX
        # BUG 一些时候没有任务可领奖，但是 attachment 中 还有 5 prize，
        # 不知道为何……
        if not self.task.finished:
            if 5 in attachment.attachment.prize_ids:
                attachment.attachment.prize_ids.remove(5)
                attachment.attachment.save()

    def has_prizes(self):
        # 是否有可领取的奖励
        return len(self.task.finished) > 0


    def trig(self, tp, times=1):
        if tp not in TASKS_ALL_TP:
            system_logger(errormsg.INVALID_OPERATE, self.char_id, "Task Trig", "invalid tp {0}".format(tp))
            return

        self.task.tasks[str(tp)] += times

        for t in self.task.doing:
            if t in self.task.complete:
                continue

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
        try:
            this_task = TASKS[_id]
        except KeyError:
            raise SanguoException(
                errormsg.TASK_NOT_EXIST,
                self.char_id,
                "Task Get Reward",
                "Task {0} not exist".format(_id)
            )

        if _id not in self.task.finished:
            raise SanguoException(
                errormsg.TASK_NOT_FINISH,
                self.char_id,
                "Task Get Reward",
                "Task {0} not finish".format(_id)
            )

        if _id in self.task.complete:
            raise SanguoException(
                errormsg.TASK_ALREADY_GOT_REWARD,
                self.char_id,
                "Task Get Reward",
                "Task {0} already got reward".format(_id)
            )

        sycee = this_task.sycee if this_task.sycee else 0
        gold = this_task.gold if this_task.gold else 0

        resource = Resource(self.char_id, "Task Reward", "task {0}".format(_id))
        standard_drop = resource.add(gold=gold, sycee=sycee)

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

        return standard_drop_to_attachment_protomsg(standard_drop)


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
            if this_task.func and not func_opened(self.char_id, this_task.func):
                # 对于没有开放功能的任务不显示
                continue

            msg_t = msg.tasks.add()
            msg_t.id = t

            current_times = self.task.tasks[str(this_task.tp)]
            if current_times > this_task.times:
                current_times = this_task.times

            msg_t.current_times = current_times

            if t in self.task.complete:
                status = MsgTask.COMPLETE
            elif t in self.task.finished:
                status = MsgTask.REWARD
            else:
                status = MsgTask.DOING

            msg_t.status = status

        publish_to_char(self.char_id, pack_msg(msg))

