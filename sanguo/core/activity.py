# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-11-4'

import operator
import json

import arrow

from django.conf import settings
from mongoengine import DoesNotExist, Q
from core.exception import SanguoException
from core.mongoscheme import MongoActivityStatic, MongoPurchaseLog, MongoCostSyceeLog
from core.server import server
from core.msgpipe import publish_to_char
from core.mail import Mail
from core.attachment import get_drop, standard_drop_to_attachment_protomsg, make_standard_drop_from_template
from core.resource import Resource
from utils import pack_msg

from preset.data import ACTIVITY_STATIC, ACTIVITY_STATIC_CONDITIONS
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
            if isinstance(self.start_time, arrow.Arrow):
                x = self.start_time
            else:
                x = arrow.get(self.start_time)
            init_date = arrow.Arrow(
                year=x.year,
                month=x.month,
                day=x.day,
                hour=x.hour,
                minute=0,
                second=0,
                tzinfo=x.tzinfo,
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


def get_mongo_activity_instance(char_id):
    # 获取mongodb中的 记录
    try:
        mongo_ac = MongoActivityStatic.objects.get(id=char_id)
    except DoesNotExist:
        mongo_ac = MongoActivityStatic(id=char_id)
        mongo_ac.reward_times = {}
        mongo_ac.send_times = {}
        mongo_ac.save()

    return mongo_ac


class _Activities(object):
    def __init__(self):
        self.items = {}

    def __getitem__(self, item):
        return self.items[item]

    def register(self, activity_id):
        if activity_id in self.items:
            raise RuntimeError("{0} already registed!".format(activity_id))

        def deco(cls):
            cls.ACTIVITY_ID = activity_id
            self.items[activity_id] = cls
            def wrap():
                return cls()
            return wrap
        return deco

activities = _Activities()

class ActivityTriggerManually(object):
    # 需要手动领奖的
    def trig(self, char_id):
        pass

    def get_reward(self, char_id, condition_id):
        # 领取奖励
        self.get_reward_check(char_id, condition_id)
        return self.get_reward_done(char_id, condition_id)


    def get_reward_check(self, char_id, condition_id):
        is_passed = self.condition_is_passed(char_id, condition_id)
        if not is_passed:
            raise SanguoException(
                errormsg.ACTIVITY_CAN_NOT_GET_REWARD,
                char_id,
                "Activity Get Reward",
                "condition {0} can not get".format(condition_id)
            )

        mongo_ac = get_mongo_activity_instance(char_id)
        if str(condition_id) in mongo_ac.send_times:
            raise SanguoException(
                errormsg.ACTIVITY_ALREADY_GOT_REWARD,
                char_id,
                "Activity Get Reward",
                "condition {0} already got".format(condition_id)
            )

        mongo_ac.reward_times[str(condition_id)] = 1
        mongo_ac.save()


    def get_reward_done(self, char_id, condition_id):
        standard_drop = get_drop([ACTIVITY_STATIC_CONDITIONS[condition_id].package])
        resource = Resource(char_id, "Activity Get Reward", "get condition id {0}".format(condition_id))
        standard_drop = resource.add(**standard_drop)

        return standard_drop_to_attachment_protomsg(standard_drop)


class ActivityTriggerMail(object):
    # 自动发邮件的
    def trig(self, char_id):
        value = self.get_current_value(char_id)
        passed, not_passed = self.select_conditions(value)

        if not passed:
            return

        passed = self.get_passed_for_send_mail(passed)
        mongo_ac = get_mongo_activity_instance(char_id)

        for p in passed:
            if str(p) in mongo_ac.send_times:
                continue

            mail = Mail(char_id)
            mail.add(
                self.get_mail_title(p),
                self.get_mail_content(p),
                attachment=self.get_mail_attachment(p)
            )

            mongo_ac.send_times[str(p)] = 1

        mongo_ac.save()

    def get_passed_for_send_mail(self, passed):
        return passed


    def get_mail_title(self, p):
        return self.activity_data.mail_title.format(ACTIVITY_STATIC_CONDITIONS[p].condition_value)

    def get_mail_content(self, p):
        return self.activity_data.mail_content.format(ACTIVITY_STATIC_CONDITIONS[p].condition_value)

    def get_mail_attachment(self, p):
        drop = get_drop([ACTIVITY_STATIC_CONDITIONS[p].package])
        return json.dumps(drop)


    def get_reward(self, char_id, condition_id):
        raise SanguoException(
            errormsg.ACTIVITY_GET_REWARD_TP_ERROR,
            char_id,
            "Activity Get Reward",
            "condition {0} can not get".format(condition_id)
        )


class ActivityTriggerAdditionalDrop(object):
    # 操作的额外加成
    def get_additional_drop(self, *args, **kwargs):
        if not self.is_valid():
            return make_standard_drop_from_template()

        package_id = self.activity_data.package
        return get_drop([package_id])



class ActivityBase(object):
    OPERATOR = operator.ge
    ACTIVITY_ID = 0

    def __init__(self):
        self.activity_id = self.ACTIVITY_ID
        self.activity_data = ACTIVITY_STATIC[self.activity_id]

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
        # 这是对于数值大于小于这类条件活动的，
        # 其他类型的，在子类中重写
        passed = []
        not_passed = []

        for c in self.activity_data.condition_objs:
            if self.OPERATOR(value, c.condition_value):
                passed.append(c.id)
            else:
                not_passed.append(c.id)

        return passed, not_passed

    def condition_is_passed(self, char_id, condition_id):
        value = self.get_current_value(char_id)
        passed, not_passed = self.select_conditions(value)
        return condition_id in passed


    def get_current_value(self, char_id):
        raise NotImplementedError()


@activities.register(1001)
class Activity1001(ActivityBase, ActivityTriggerManually):
    # 角色等级
    def get_current_value(self, char_id):
        from core.character import Char
        return Char(char_id).mc.level

@activities.register(2001)
class Activity2001(ActivityBase, ActivityTriggerManually):
    # 武将召唤（甲将数量）
    def get_current_value(self, char_id):
        from core.hero import char_heros_amount
        return char_heros_amount(char_id, filter_quality=1)

@activities.register(3001)
class Activity3001(ActivityBase, ActivityTriggerManually):
    # 通过战役
    def get_current_value(self, char_id):
        from core.stage import Stage
        return Stage(char_id).get_passed_max_battle_id()

@activities.register(4001)
class Activity4001(ActivityBase, ActivityTriggerMail):
    # 比武周排名
    OPERATOR = operator.le

    def get_activity_time(self):
        # 如果是周六，周日开服，那么就当成下周一开服
        # 并且肯定是continued到周日24：00
        t = ActivityBase.get_activity_time(self)
        weekday = t.init_date.weekday()
        if weekday == 5 or weekday == 6:
            days = 7 - weekday
            new_start_time = t.init_date.replace(days=days).replace(tzinfo=settings.TIME_ZONE).to('UTC')
            continued_days = 7
        else:
            new_start_time = t.init_date
            continued_days = 7 - weekday

        t = ActivityTime(
            new_start_time,
            continued_days,
            self.activity_data.interval_days,
            self.activity_data.interval_times
        )

        return t

    def get_current_value(self, char_id):
        from core.arena import Arena
        return Arena(char_id).rank

    def get_passed_for_send_mail(self, passed):
        passed_conditions = [ACTIVITY_STATIC_CONDITIONS[i] for i in passed]
        passed_conditions.sort(key=lambda item: item.condition_value)

        p = passed_conditions[0]
        return [p]



@activities.register(5001)
class Activity5001(ActivityBase, ActivityTriggerMail):
    # 累计充值
    def get_current_value(self, char_id):
        if not self.is_valid():
            return 0

        condition = Q(char_id=char_id) & Q(purchase_at__gte=self.activity_time.nearest_open_date.timestamp) & Q(purchase_at__lte=self.activity_time.nearest_close_date.timestamp)
        logs = MongoPurchaseLog.objects.filter(condition)

        value = 0
        for log in logs:
            value += log.sycee

        return value

@activities.register(6001)
class Activity6001(ActivityBase, ActivityTriggerMail):
    # 累计消费元宝
    def get_current_value(self, char_id):
        if not self.is_valid():
            return 0

        condition = Q(char_id=char_id) & Q(cost_at__gte=self.activity_time.nearest_open_date.timestamp) & Q(cost_at__lte=self.activity_time.nearest_close_date.timestamp)
        logs = MongoCostSyceeLog.objects.filter(condition)

        value = 0
        for log in logs:
            value += log.sycee

        return value


@activities.register(7001)
class Activity7001(ActivityBase, ActivityTriggerManually):
    # 累计汤圆 stuff_id = 3003
    STUFF_ID = 3003
    def get_current_value(self, char_id):
        from core.item import Item
        item = Item(char_id)
        return item.stuff_amount(self.STUFF_ID)


    def get_reward_check(self, char_id, condition_id):
        value = ACTIVITY_STATIC_CONDITIONS[condition_id].condition_value
        resource = Resource(char_id, "Activity Get Reward 7001")
        resource.check_and_remove(stuffs=[(self.STUFF_ID, value)])


@activities.register(8001)
class Activity8001(ActivityBase, ActivityTriggerManually):
    # 收集五虎上将
    def get_current_value(self, char_id):
        from core.hero import char_heros_dict

        heros = char_heros_dict(char_id)
        hero_oids = [h.oid for h in heros.values()]

        condition_ids = self.activity_data.condition_objs[0].condition_ids
        need_hero_ids = [int(i) for i in condition_ids.split(',')]

        value = 0
        for hid in need_hero_ids:
            if hid in hero_oids:
                value += 1

        return value


@activities.register(9001)
class Activity9001(ActivityBase, ActivityTriggerAdditionalDrop):
    def get_current_value(self, char_id):
        return 0


@activities.register(10001)
class Activity10001(ActivityBase, ActivityTriggerAdditionalDrop):
    def get_additional_drop(self, stuff_id):
        if stuff_id != 33:
            return make_standard_drop_from_template()
        return ActivityTriggerAdditionalDrop.get_additional_drop(self)

    def get_current_value(self, char_id):
        return 0


@activities.register(11001)
class Activity11001(ActivityBase, ActivityTriggerAdditionalDrop):
    def get_current_value(self, char_id):
        return 0




# 活动类的统一入口
class ActivityEntry(object):
    def __new__(cls, activity_id):
        return activities[activity_id]()


class ActivityStatic(object):
    def __init__(self, char_id):
        self.char_id = char_id


    def trig(self, activity_id):
        entry = ActivityEntry(activity_id)
        if not entry.is_valid():
            return

        entry.trig(self.char_id)

        self.send_update_notify([activity_id])


    def get_reward(self, condition_id):
        activity_id = ACTIVITY_STATIC_CONDITIONS[condition_id].activity_id
        entry = ActivityEntry(activity_id)
        msg = entry.get_reward(self.char_id, condition_id)

        self.send_update_notify([activity_id])
        return msg


    def is_show(self, activity_id):
        # 是否显示
        entry = ActivityEntry(activity_id)
        if entry.is_valid():
            # 此活动还在进行中
            return True

        if entry.activity_data.category != 1:
            # 非开服活动，只要过期就算还有奖励没领，也不再显示
            return False

        condition_ids = entry.get_condition_ids()
        if not condition_ids:
            # 过期，并且只是介绍性质的活动
            return False

        if entry.activity_data.mode == 1:
            # 手动领取奖励
            mongo_ac = get_mongo_activity_instance(self.char_id)
            for _con_id in condition_ids:
                if str(_con_id) not in mongo_ac.reward_times and entry.condition_is_passed(self.char_id, _con_id):
                    # 还有已经完成，但是没领的奖励
                    return True

        return False


    def _msg_activity(self, msg, activity_id):
        mongo_ac = get_mongo_activity_instance(self.char_id)

        entry = ActivityEntry(activity_id)

        msg.id = activity_id
        msg.current_value = entry.get_current_value(self.char_id)
        msg.left_time = entry.left_time

        for i in entry.get_condition_ids():
            msg_condition = msg.conditions.add()
            msg_condition.id = i

            if str(i) in mongo_ac.reward_times:
                status = ActivityEntryMsg.ActivityCondition.HAS_GOT
            elif entry.condition_is_passed(self.char_id, i):
                status = ActivityEntryMsg.ActivityCondition.CAN_GET
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
            if not force_send and not self.is_show(i):
                continue

            msg_activity = msg.activities.add()
            self._msg_activity(msg_activity, i)

        publish_to_char(self.char_id, pack_msg(msg))


