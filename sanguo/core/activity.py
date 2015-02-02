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



class ActivityEntry(object):
    __slots__ = ['activity_id', 'activity_data']
    def __init__(self, activity_id):
        self.activity_id = activity_id
        self.activity_data=  ACTIVITY_STATIC[activity_id]

    @property
    def continued_to(self):
        # 活动持续到什么时间
        if self.activity_data.start_time:
            x = arrow.get(self.activity_data.start_time)
            start_time = arrow.Arrow(
                year=x.year,
                month=x.month,
                day=x.day,
                hour=x.hour,
                minute=0,
                second=0,
            )
        else:
            start_time = server.opened_date.replace(tzinfo=settings.TIME_ZONE)

        if self.activity_data.tp != 4:
            return start_time.replace(hours=+self.activity_data.total_continued_hours)

        # 周比武奖励，结束时间是开服后遇到的第一个周日24：00过后
        start_weekday = start_time.weekday()
        day_needs = 6 - start_weekday
        if day_needs == 0:
            # 如果是周日开服，就把结束日期放到下个周日
            day_needs = 7
        if day_needs == 1:
            # 同上，放到下个周日
            day_needs = 8

        # day_needs 还得+1, 要放到周一的00：00点
        day_needs += 1

        start_time = start_time.replace(days=day_needs)
        return arrow.Arrow(
            year=start_time.year,
            month=start_time.month,
            day=start_time.day,
            minute=0,
            second=0,
        )

    @property
    def started(self):
        # 是否开始了
        if not self.activity_data.start_time:
            return True

        start_at = arrow.get(self.activity_data.start_time)
        return arrow.utcnow() >= start_at

    @property
    def ended(self):
        # 是否结束了
        return arrow.utcnow() > self.continued_to

    @property
    def left_time(self):
        t = self.continued_to.timestamp - arrow.utcnow().timestamp
        return t if t > 0 else 0

    def is_valid(self):
        return self.started and not self.ended

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
        # 当前值
        # 1: 角色等级
        # 2: 武将召唤（甲将数量）
        # 3: 通过战役
        # 4: 比武周排名

        from core.character import Char
        from core.hero import char_heros_amount
        from core.stage import Stage
        from core.arena import Arena

        if self.activity_data.tp == 1:
            return Char(char_id).mc.level

        if self.activity_data.tp == 2:
            return char_heros_amount(char_id, filter_quality=1)

        if self.activity_data.tp == 3:
            return Stage(char_id).get_passed_max_battle_id()

        if self.activity_data.tp == 4:
            return Arena(char_id).rank

        raise RuntimeError("Unknown Activity tp: {0}".format(self.activity_data.tp))



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

            mail = Mail(self.char_id)
            mail.add(
                MAIL_ACTIVITY_ARENA_TITLE.format(value),
                MAIL_ACTIVITY_ARENA_CONTENT.format(value),
                attachment=json.dumps(PACKAGES[p.package])
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


