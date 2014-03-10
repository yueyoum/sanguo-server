# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/12/14'

from mongoscheme import DoesNotExist
from core.mongoscheme import MongoAchievement
from core.attachment import Attachment

from apps.achievement.models import Achievement as ModelAchievement

from core.msgpipe import publish_to_char
from utils import pack_msg

from protomsg import AchievementNotify, UpdateAchievementNotify
from protomsg import Achievement as MsgAchievement
from protomsg import Attachment as MsgAttachment

from core.exception import InvalidOperate


class Achievement(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.achievement = MongoAchievement.objects.get(id=char_id)
        except DoesNotExist:
            self.achievement = MongoAchievement(id=char_id)
            self.achievement.doing = {}
            self.achievement.finished = []
            self.achievement.complete = []
            self.achievement.save()


    def trig(self, condition_id, new_value=None):
        achs = ModelAchievement.get_all_by_conditions()[condition_id]
        for a in achs:
            self.trig_by_achievement(a, new_value=new_value)

    def trig_by_achievement(self, ach, new_value=None):
        achievement_id = ach.id
        if achievement_id in self.achievement.complete or achievement_id in self.achievement.finished:
            return

        attachment = Attachment(self.char_id)
        str_id = str(achievement_id)

        decoded_condition_value = ach.decoded_condition_value()

        if ach.mode == 1:
            if new_value not in decoded_condition_value:
                return

            if str_id in self.achievement.doing:
                values = [int(i) for i in self.achievement.doing[str_id].split(',')]
            else:
                values = []

            if new_value not in values:
                values.append(new_value)

            if set(values) == set(decoded_condition_value):
                # FINISH
                self.achievement.finished.append(achievement_id)
                self.achievement.doing.pop(str_id)
                attachment.save_to_prize(4)
            else:
                self.achievement.doing[str_id] = ','.join([str(i) for i in values])

        elif ach.mode == 2:
            if new_value != decoded_condition_value:
                return
            # FINISH
            self.achievement.finished.append(achievement_id)
            attachment.save_to_prize(4)

        else:
            if str_id in self.achievement.doing:
                value = self.achievement.doing[str_id]
            else:
                value = 0

            value += new_value
            if new_value >= ach.decoded_condition_value():
                # FINISH
                self.achievement.finished.append(achievement_id)
                if str_id in self.achievement.doing:
                    self.achievement.doing.pop(str_id)
                attachment.save_to_prize(4)
            else:
                self.achievement.doing[str_id] = value

        self.achievement.save()

        msg = UpdateAchievementNotify()
        self._fill_up_achievement_msg(msg.achievement, ach)
        publish_to_char(self.char_id, pack_msg(msg))


    def get_reward(self, achievement_id):
        if achievement_id not in self.achievement.finished:
            raise InvalidOperate("Achievement Get Reward: Char {0} try to get achievement {1}. But this achievement not finished".format(self.char_id, achievement_id))

        try:
            ach = ModelAchievement.all()[achievement_id]
        except KeyError:
            raise InvalidOperate("Achievement Get Reward: Char {0} try to get a NONE exists achievement {1}".format(self.char_id, achievement_id))

        from core.character import Char
        char = Char(self.char_id)
        char.update(sycee=ach.sycee, des='Achievement {0} reward'.format(achievement_id))

        self.achievement.finished.remove(achievement_id)
        self.achievement.complete.append(achievement_id)
        self.achievement.save()

        msg = UpdateAchievementNotify()
        self._fill_up_achievement_msg(msg.achievement, ach)
        publish_to_char(self.char_id, pack_msg(msg))

        msg = MsgAttachment()
        msg.sycee = ach.sycee
        return msg



    def send_notify(self):
        all_achievements = ModelAchievement.all()

        msg = AchievementNotify()
        for v in all_achievements.values():
            a = msg.achievements.add()
            self._fill_up_achievement_msg(a, v)

        publish_to_char(self.char_id, pack_msg(msg))


    def _fill_up_achievement_msg(self, msg, ach):
        msg.id = ach.id
        if ach.id in self.achievement.finished:
            status = MsgAchievement.REWARD
        elif ach.id in self.achievement.complete:
            status = MsgAchievement.COMPLETE
        else:
            status = MsgAchievement.DOING

        msg.status = status

        decoded_condition_value = ach.decoded_condition_value()

        if ach.mode == 1:
            msg.mach.condition.extend(decoded_condition_value)
            if msg.status == MsgAchievement.DOING:
                if str(ach.id) in self.achievement.doing:
                    msg.mach.current.extend([int(i) for i in self.achievement.doing[str(ach.id)].split(',')])
            else:
                msg.mach.current.extend(decoded_condition_value)

        elif ach.mode == 2:
            msg.sach.condition = decoded_condition_value

        else:
            msg.cach.condition = decoded_condition_value
            if msg.status == MsgAchievement.DOING:
                if str(ach.id) in self.achievement.doing:
                    msg.cach.current = int(self.achievement.doing[str(ach.id)])
                else:
                    msg.cach.current = 0
            else:
                msg.cach.current = decoded_condition_value

