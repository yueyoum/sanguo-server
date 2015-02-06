# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-11-4'

import operator
import json

import arrow

from django.conf import settings
from mongoengine import DoesNotExist
from core.exception import SanguoException
from core.mongoscheme import MongoActivityStatic
from core.server import server
from core.msgpipe import publish_to_char
from core.mail import Mail
from core.attachment import get_drop, standard_drop_to_attachment_protomsg
from core.resource import Resource
from utils import pack_msg

from preset.data import ACTIVITY_STATIC, ACTIVITY_STATIC_CONDITIONS, PACKAGES
from preset.settings import MAIL_ACTIVITY_ARENA_TITLE, MAIL_ACTIVITY_ARENA_CONTENT
from preset import errormsg

from protomsg import ActivityNotify, ActivityUpdateNotify, ActivityEntry as ActivityEntryMsg



class ActivityTime(object):
    def __init__(self, start_time, continued_days, interval_days, interval_times, now=None):
        self.start_time = start_time
        self.continued_days = continued_days
        self.interval_days = interval_days
        self.interval_times = interval_times

        if not now:
            self.now = arrow.utcnow()
        else:
            self.now = arrow.get(now)

        # 首次开始日期
        self.init_date = self.get_init_date()
        # 最近一次的开始日期
        self.nearest_open_date = self.find_nearest_open_date()
        # 最近一次的关闭日期
        self.nearest_close_date = self.find_nearest_close_date()

        # 距离最近一次活动关闭的剩余秒数
        left_time = self.nearest_close_date.timestamp - self.now.timestamp
        self.left_time = left_time if left_time > 0 else 0

        # 是否处于活动时间范围内
        self.is_valid = self.now >= self.nearest_open_date and self.now < self.nearest_close_date


    def get_init_date(self):
        if self.start_time:
            x = arrow.get(self.start_time)
            init_date = arrow.Arrow(
                year=x.year,
                month=x.month,
                day=x.day,
                hour=x.hour,
                minute=0,
                second=0,
            )
        else:
            init_date = server.opened_date.replace(tzinfo=settings.TIME_ZONE)

        return init_date


    def find_nearest_open_date(self):
        if not self.interval_days:
            return self.init_date

        # 目前超过初始日期的天数
        beyond_days = (self.now - self.init_date).days
        # 活动一次开启间隔要持续的天数
        total_days = self.continued_days + self.interval_days

        # 和目前最近的开启日期，需要此活动开启的次数
        open_times, _rest = divmod(beyond_days, total_days)

        if not self.interval_times:
            # 此活动无限重复
            really_open_times = open_times
        else:
            if self.interval_times >= open_times:
                really_open_times = open_times
            else:
                really_open_times = self.interval_times

        return self.init_date.replace(days=really_open_times*total_days)


    def find_nearest_close_date(self):
        return self.nearest_open_date.replace(days=self.continued_days)




class ActivityBase(object):
    def __init__(self, activity_id):
        self.activity_id = activity_id
        self.activity_data = ACTIVITY_STATIC[activity_id]

        self.activity_time = self.get_activity_time()

    def get_activity_time(self):
        return ActivityTime(
            self.activity_data.start_time,
            self.activity_data.continued_days,
            self.activity_data.interval_days,
            self.activity_data.interval_times,
        )


    @property
    def left_time(self):
        return self.activity_time.left_time

    def is_valid(self):
        return self.activity_time.is_valid

    def get_condition_ids(self):
        return [obj.id for obj in self.activity_data.condition_objs]

    def select_conditions(self, value):
        passed = []
        not_passed = []

        ope = operator.ge if self.activity_data.condition_type == 1 else operator.le
        for c in self.activity_data.condition_objs:
            if ope(value, c.condition_value):
                passed.append(c.id)
            else:
                not_passed.append(c.id)

        return passed, not_passed

    def get_current_value(self, char_id):
        raise NotImplementedError()


class ActivityType_1(ActivityBase):
    # 角色等级
    def get_current_value(self, char_id):
        from core.character import Char
        return Char(char_id).mc.level

class ActivityType_2(ActivityBase):
    # 武将召唤（甲将数量）
    def get_current_value(self, char_id):
        from core.hero import char_heros_amount
        return char_heros_amount(char_id, filter_quality=1)

class ActivityType_3(ActivityBase):
    # 通过战役
    def get_current_value(self, char_id):
        from core.stage import Stage
        return Stage(char_id).get_passed_max_battle_id()


class ActivityType_4(ActivityBase):
    # 比武周排名
    def get_activity_time(self):
        # 如果是周六，周日开服，那么就当成下周一开服
        t = super(ActivityType_4, self).get_activity_time()
        weekday = t.init_date.weekday()
        if weekday == 5 or weekday == 6:
            days = 7 - weekday
            new_start_time = t.init_date.replace(days=days).format('YYYY-MM-DD')
            t = ActivityTime(
                new_start_time,
                self.activity_data.continued_days,
                self.activity_data.interval_days,
                self.activity_data.interval_times
            )

        return t

    def get_current_value(self, char_id):
        from core.arena import Arena
        return Arena(char_id).rank


class ActivityEntry(object):
    def __new__(cls, activity_id):
        data = ACTIVITY_STATIC[activity_id]
        if data.tp == 1:
            return ActivityType_1(activity_id)
        if data.tp == 2:
            return ActivityType_2(activity_id)
        if data.tp == 3:
            return ActivityType_3(activity_id)
        if data.tp == 4:
            return ActivityType_4(activity_id)



class ActivityStatic(object):
    def __init__(self, char_id):
        self.char_id = char_id

        try:
            self.mongo_ac = MongoActivityStatic.objects.get(id=self.char_id)
        except DoesNotExist:
            self.mongo_ac = MongoActivityStatic(id=self.char_id)
            self.mongo_ac.can_get = []
            self.mongo_ac.reward_times = {}
            self.mongo_ac.send_times = {}
            self.mongo_ac.save()


    def trig(self, activity_tp_id):
        if activity_tp_id == 4:
            # 只发邮件，不触发
            return

        activities = []

        for ac in ACTIVITY_STATIC.values():
            if ac.tp != activity_tp_id:
                continue

            activities.append(ac.id)
            entry = ActivityEntry(ac.id)
            if not entry.is_valid():
                # 过期了
                continue

            value = entry.get_current_value(self.char_id)
            passed, not_passed = entry.select_conditions(value)

            for p in passed:
                if str(p) not in self.mongo_ac.reward_times and p not in self.mongo_ac.can_get:
                    self.mongo_ac.can_get.append(p)

        self.mongo_ac.save()
        self.send_update_notify(activities)


    def send_mail(self):
        # 这里就是处理特殊的tp==4的发邮件

        activities = []
        for k, v in ACTIVITY_STATIC.iteritems():
            if v.tp == 4:
                activities.append(k)

        for ac in activities:
            entry = ActivityEntry(ac)

            if not entry.is_valid():
                # 这组活动不可用
                continue

            value = entry.get_current_value(self.char_id)
            passed, not_passed = entry.select_conditions(value)
            if not passed:
                continue

            for i in self.mongo_ac.send_times.keys():
                if int(i) in passed:
                    # 这一组活动已经发送过一次邮件
                    continue

            passed_conditions = [ACTIVITY_STATIC_CONDITIONS[i] for i in passed]
            passed_conditions.sort(key=lambda item: item.condition_value)

            p = passed_conditions[0]

            standard_drop = get_drop([p.package])

            mail = Mail(self.char_id)
            mail.add(
                MAIL_ACTIVITY_ARENA_TITLE.format(value),
                MAIL_ACTIVITY_ARENA_CONTENT.format(value),
                attachment=json.dumps(standard_drop)
            )

            self.mongo_ac.send_times[str(p.id)] = 1
            self.mongo_ac.save()


    def get_reward(self, condition_id):
        if str(condition_id) in self.mongo_ac.reward_times or str(condition_id) in self.mongo_ac.send_times:
            raise SanguoException(
                errormsg.ACTIVITY_ALREADY_GOT_REWARD,
                self.char_id,
                "Activity Get Reward",
                "condition {0} already got".format(condition_id)
            )

        if condition_id not in self.mongo_ac.can_get:
            raise SanguoException(
                errormsg.ACTIVITY_CAN_NOT_GET_REWARD,
                self.char_id,
                "Activity Get Reward",
                "condition {0} can not get".format(condition_id)
            )

        activity_id = ACTIVITY_STATIC_CONDITIONS[condition_id].activity_id
        if ACTIVITY_STATIC[activity_id].tp == 4:
            # 发邮件，不能主动领取
            raise SanguoException(
                errormsg.ACTIVITY_GET_REWARD_TP_ERROR,
                self.char_id,
                "Activity Get Reward",
                "condition {0} can not get, because tp is 4".format(condition_id)
            )

        self.mongo_ac.can_get.remove(condition_id)
        self.mongo_ac.reward_times[str(condition_id)] = 1
        self.mongo_ac.save()

        self.send_update_notify([activity_id])

        standard_drop = get_drop([ACTIVITY_STATIC_CONDITIONS[condition_id].package])
        resource = Resource(self.char_id, "Activity Get Reward", "get condition id {0}".format(condition_id))
        standard_drop = resource.add(**standard_drop)

        return standard_drop_to_attachment_protomsg(standard_drop)



    def _msg_activity(self, msg, activity_id):
        entry = ActivityEntry(activity_id)

        msg.id = activity_id
        msg.current_value = entry.get_current_value(self.char_id)
        msg.left_time = entry.left_time

        for i in entry.get_condition_ids():

            msg_condition = msg.conditions.add()
            msg_condition.id = i

            if i in self.mongo_ac.can_get:
                status = ActivityEntryMsg.ActivityCondition.CAN_GET
            elif str(i) in self.mongo_ac.reward_times:
                status = ActivityEntryMsg.ActivityCondition.HAS_GOT
            else:
                status = ActivityEntryMsg.ActivityCondition.CAN_NOT

            msg_condition.status = status


    def send_update_notify(self, activity_ids):
        self.send_notify(Msg=ActivityUpdateNotify, activity_ids=activity_ids, force_send=True)


    def send_notify(self, Msg=ActivityNotify, activity_ids=None, force_send=False):
        msg = Msg()

        if not activity_ids:
            activity_ids = ACTIVITY_STATIC.keys()

        for i in activity_ids:
            entry = ActivityEntry(i)

            if not force_send:
                if ACTIVITY_STATIC[i].tp == 4:
                    if not entry.is_valid():
                        continue
                else:
                    has_reward_go_got = False
                    for _cid in entry.get_condition_ids():
                        if _cid in self.mongo_ac.can_get:
                            has_reward_go_got = True
                            break

                    if not has_reward_go_got and not entry.is_valid():
                        continue

            msg_activity = msg.activities.add()
            self._msg_activity(msg_activity, i)

        publish_to_char(self.char_id, pack_msg(msg))


