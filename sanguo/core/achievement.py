# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/12/14'

from mongoscheme import DoesNotExist
from core.mongoscheme import MongoAchievement
from core.attachment import Attachment, get_drop, standard_drop_to_attachment_protomsg, make_standard_drop_from_template
from core.resource import Resource

from core.msgpipe import publish_to_char
from utils import pack_msg

from protomsg import AchievementNotify, UpdateAchievementNotify
from protomsg import Achievement as MsgAchievement

from core.exception import SanguoException

from preset.data import ACHIEVEMENTS, ACHIEVEMENT_CONDITIONS, ACHIEVEMENT_FIRST_IDS
from preset import errormsg



class Achievement(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.achievement = MongoAchievement.objects.get(id=char_id)
        except DoesNotExist:
            self.achievement = MongoAchievement(id=char_id)
            self.achievement.doing = {}
            self.achievement.display = ACHIEVEMENT_FIRST_IDS
            self.achievement.finished = []
            self.achievement.complete = []
            self.achievement.save()



    def trig(self, condition_id, new_value, send_notify=True):
        achs = ACHIEVEMENT_CONDITIONS[condition_id]
        for a in achs:
            self.trig_achievement(a, new_value, send_notify=send_notify)


    def trig_achievement(self, ach, new_value, send_notify=True):
        achievement_id = ach.id
        if achievement_id in self.achievement.complete or achievement_id in self.achievement.finished:
            return

        attachment = Attachment(self.char_id)
        str_id = str(achievement_id)

        decoded_condition_value = ach.decoded_condition_value


        def finish_it():
            if achievement_id not in self.achievement.finished:
                self.achievement.finished.append(achievement_id)
            if str_id in self.achievement.doing:
                self.achievement.doing.pop(str_id)

            if achievement_id in self.achievement.display:
                attachment.save_to_prize(4)


        if ach.mode == 1:
            # 多个ID条件
            actual_new_value = [i for i in new_value if i in decoded_condition_value]
            if not actual_new_value:
                return

            if str_id in self.achievement.doing:
                values = [int(i) for i in self.achievement.doing[str_id].split(',')]
            else:
                values = []

            for av in actual_new_value:
                if av not in values:
                    values.append(av)

            if set(values) == set(decoded_condition_value):
                # FINISH
                finish_it()
            else:
                self.achievement.doing[str_id] = ','.join([str(i) for i in values])

        elif ach.mode == 2:
            # 单个ID条件
            if new_value != decoded_condition_value:
                return
            # FINISH
            finish_it()

        elif ach.mode == 3:
            # 普通数量条件 数量累加
            if str_id in self.achievement.doing:
                value = self.achievement.doing[str_id]
            else:
                value = 0

            value += new_value
            if value >= decoded_condition_value:
                # FINISH
                finish_it()
            else:
                self.achievement.doing[str_id] = value

        elif ach.mode == 4:
            # 阀值数量条件
            # 这里不叠加，只是简单的比较
            if new_value >= decoded_condition_value:
                # FINISH
                finish_it()
            else:
                self.achievement.doing[str_id] = new_value

        else:
            # 反向阀值条件， 比较小于就完成
            if new_value <= decoded_condition_value:
                # FINISH
                finish_it()
            else:
                self.achievement.doing[str_id] = new_value

        self.achievement.save()


        if send_notify and achievement_id in self.achievement.display:
            msg = UpdateAchievementNotify()
            self._fill_up_achievement_msg(msg.achievement, ach)
            publish_to_char(self.char_id, pack_msg(msg))


    def get_reward(self, achievement_id):
        try:
            ach = ACHIEVEMENTS[achievement_id]
        except KeyError:
            raise SanguoException(
                errormsg.ACHIEVEMENT_NOT_EXIST,
                self.char_id,
                "Achievement Get Reward",
                "{0} not exist".format(achievement_id)
            )

        if achievement_id not in self.achievement.display:
            raise SanguoException(
                errormsg.ACHIEVEMENT_NOT_FINISH,
                self.char_id,
                "Achievement Get Reward",
                "{0} not in display".format(achievement_id)
            )

        if achievement_id not in self.achievement.finished:
            raise SanguoException(
                errormsg.ACHIEVEMENT_NOT_FINISH,
                self.char_id,
                "Achievement Get Reward",
                "{0} not finished".format(achievement_id)
            )

        self.achievement.finished.remove(achievement_id)
        self.achievement.complete.append(achievement_id)

        updated_achs = [ach]

        if ach.next:
            index = self.achievement.display.index(achievement_id)
            self.achievement.display.pop(index)
            self.achievement.display.insert(index, ach.next)

            updated_achs.append(ACHIEVEMENTS[ach.next])

            if ach.next in self.achievement.finished:
                attachment = Attachment(self.char_id)
                attachment.save_to_prize(4)

        self.achievement.save()

        for up_ach in updated_achs:
            msg = UpdateAchievementNotify()
            self._fill_up_achievement_msg(msg.achievement, up_ach)
            publish_to_char(self.char_id, pack_msg(msg))

        standard_drop = self.send_reward(achievement_id, ach.sycee, ach.package)
        return standard_drop_to_attachment_protomsg(standard_drop)


    def send_reward(self, aid, sycee, packages):
        if not sycee and not packages:
            return make_standard_drop_from_template()

        if packages:
            ps = [int(i) for i in packages.split(',')]
        else:
            ps = []

        drops = get_drop(ps)
        drops['sycee'] += sycee if sycee else 0

        resource = Resource(self.char_id, "Achievement Reward", "achievement {0}".format(aid))
        drops = resource.add(**drops)
        return drops


    def send_notify(self):
        msg = AchievementNotify()
        for v in ACHIEVEMENTS.values():
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
        msg.show = ach.id in self.achievement.display

        decoded_condition_value = ach.decoded_condition_value

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

