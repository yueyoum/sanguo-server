# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-11-4'

import operator
import json

import arrow

from django.conf import settings
from mongoengine import DoesNotExist, Q
from core.exception import SanguoException
from core.mongoscheme import MongoActivityStatic, MongoPurchaseLog, MongoCostSyceeLog, MongoCharacter
from core.server import server
from core.character import get_char_property
from core.msgpipe import publish_to_char
from core.mail import Mail
from core.attachment import get_drop, standard_drop_to_attachment_protomsg, make_standard_drop_from_template
from core.resource import Resource
from core.times_log import (
    TimesLogLogin,
    TimesLogEliteStage,
    TimesLogEquipStepUp,
    TimesLogGetHeroBySycee,
    TimesLogHeroStepUp,
    TimesLogPlunder,
)

from core.purchase import BasePurchaseAction

from utils import pack_msg

from preset.data import ACTIVITY_STATIC, ACTIVITY_STATIC_CONDITIONS
from preset.settings import ACTIVITY_STAGE_MAX_TIMES
from preset import errormsg

from protomsg import ActivityNotify, ActivityUpdateNotify, ActivityEntry as ActivityEntryMsg


class ActivityConditionRecord(object):
    # 记录活动领取/发放了哪些奖励，避免重复领取/发放
    # 注意：现在活动可以不间断循环开启，
    # 也就是A活动的一个周期结束后，新一轮活动会立即开启
    # 这样以前的 cron/clean_expired_activites就没法用了
    # 因为这个定时任务会一直判断这个A活动是正在进行的
    # 当新一轮活动开始后，玩家将无法领奖
    # 已经判断到已经发过了（上一轮发的）
    # 所以这里处理，把条件ID加上loop id作为唯一标识
    def __init__(self, char_id, condition_id, active_time):
        """

        :type active_time: ActivityTime
        """
        self.char_id = char_id
        self.condition_id = str(condition_id)
        self.loop_times = active_time.loop_times
        self.open_time = active_time.nearest_open_date.timestamp

        self.key = "{0}#{1}#{2}".format(self.condition_id, self.loop_times, self.open_time)

        try:
            self.mongo = MongoActivityStatic.objects.get(id=char_id)
        except DoesNotExist:
            self.mongo = MongoActivityStatic(id=char_id)
            self.mongo.reward_times = {}
            self.mongo.send_times = {}
            self.mongo.save()

        self.clean()


    @classmethod
    def fix(cls, char_id):
        for k, v in ACTIVITY_STATIC.iteritems():
            if v.condition_objs:
                ae = ActivityEntry(char_id, k)

                for c in v.condition_objs:
                    cls(char_id, c.id, ae.activity_time)

        # NOTE FUCK
        # 17002 累计充值送月卡是特殊处理的
        x = Activity17002(char_id)
        cls(char_id, x.CONDITION_ID, x.activity_time)

    def send_times(self):
        return self.mongo.send_times.get(self.key, 0)

    def reward_times(self):
        return self.mongo.reward_times.get(self.key, 0)

    def in_send(self):
        return self.key in self.mongo.send_times

    def in_reward(self):
        return self.key in self.mongo.reward_times

    def add_send(self, times=1):
        self.mongo.send_times[self.key] = self.send_times() + times
        self.mongo.save()

    def add_reward(self, times=1):
        self.mongo.reward_times[self.key] = self.reward_times() + times
        self.mongo.save()


    def clean(self):
        # 清理过期的记录
        for k, v in self.mongo.send_times.items():
            key = k.rsplit('#', 2)
            if len(key) == 1:
                if k != self.condition_id:
                    continue

                # 以前的情况，没有记录loop times的
                new_key = "{0}#{1}#{2}".format(k, self.loop_times, self.open_time)
                self.mongo.send_times.pop(k)
                self.mongo.send_times[new_key] = v
            else:
                # 现在记录了loop times的
                oid, loop_times, open_time = key
                if oid != self.condition_id:
                    continue

                # 找到这个ID的条件，然后比较open time,
                # 不一样的就删除
                if int(open_time) != self.open_time:
                    self.mongo.send_times.pop(k)


        for k, v in self.mongo.reward_times.items():
            key = k.rsplit('#', 2)
            if len(key) == 1:
                if k != self.condition_id:
                    continue

                new_key = "{0}#{1}#{2}".format(k, self.loop_times, self.open_time)
                self.mongo.reward_times.pop(k)
                self.mongo.reward_times[new_key] = v
            else:
                oid, loop_times, open_time = key
                if oid != self.condition_id:
                    continue

                if int(open_time) != self.open_time:
                    self.mongo.reward_times.pop(k)

        self.mongo.save()



class ActivityTime(object):
    def __init__(self, start_time, continued_days, is_loop, interval_days, interval_times):
        self.start_time = start_time
        self.continued_days = continued_days
        self.is_loop = is_loop
        self.interval_days = interval_days
        self.interval_times = interval_times

        self.now = arrow.utcnow().to(settings.TIME_ZONE)

        # 循环开启次数
        self.loop_times = 0
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
                init_date = self.start_time
            else:
                x = arrow.get(self.start_time)
                init_date = arrow.Arrow(
                    year=x.year,
                    month=x.month,
                    day=x.day,
                    hour=0,
                    minute=0,
                    second=0,
                ).replace(tzinfo=settings.TIME_ZONE)
        else:
            init_date = server.opened_date

        return init_date


    def find_nearest_open_date(self):
        if not self.is_loop:
            return self.init_date

        # 目前超过初始日期的天数
        beyond_days = (self.now - self.init_date).days
        # 活动一次开启间隔要持续的天数
        total_days = self.continued_days + self.interval_days

        # 和目前最近的开启日期，需要此活动开启的次数
        self.loop_times, _rest = divmod(beyond_days, total_days)

        if not self.interval_times:
            # 此活动无限重复
            really_open_times = self.loop_times
        else:
            if self.interval_times >= self.loop_times:
                really_open_times = self.loop_times
            else:
                really_open_times = self.interval_times

        return self.init_date.replace(days=really_open_times*total_days)


    def find_nearest_close_date(self):
        return self.nearest_open_date.replace(days=self.continued_days)



class _Activities(object):
    def __init__(self):
        self.items = {}

    def __getitem__(self, item):
        return self.items[item]

    def register(self, activity_id):
        if activity_id in self.items:
            raise RuntimeError("{0} already registered!".format(activity_id))

        def deco(cls):
            cls.ACTIVITY_ID = activity_id
            self.items[activity_id] = cls
            def wrap(*args, **kwargs):
                return cls(*args, **kwargs)
            return wrap
        return deco

activities = _Activities()

class ActivityTriggerManually(object):
    # 需要手动领奖的
    def trig(self, *args):
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

        ac_record = ActivityConditionRecord(char_id, condition_id, self.activity_time)
        if ac_record.in_reward():
            raise SanguoException(
                errormsg.ACTIVITY_ALREADY_GOT_REWARD,
                char_id,
                "Activity Get Reward",
                "condition {0} already got".format(condition_id)
            )

        ac_record.add_reward()


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

        for p in passed:
            ac_record = ActivityConditionRecord(char_id, p, self.activity_time)
            if ac_record.in_send():
                continue

            mail = Mail(char_id)
            mail.add(
                self.get_mail_title(p),
                self.get_mail_content(p),
                attachment=self.get_mail_attachment(p)
            )

            ac_record.add_send()


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



class PurchaseCurrentValue(object):
    def get_current_value(self, char_id):
        if not self.is_valid():
            return 0

        condition = Q(char_id=char_id) & Q(purchase_at__gte=self.activity_time.nearest_open_date.timestamp) & Q(purchase_at__lte=self.activity_time.nearest_close_date.timestamp)
        logs = MongoPurchaseLog.objects.filter(condition)

        value = 0
        for log in logs:
            value += log.sycee

        return value


class ActivityBase(object):
    OPERATOR = operator.ge
    ACTIVITY_ID = 0

    def __init__(self, char_id):
        self.char_id = char_id
        self.activity_id = self.ACTIVITY_ID
        self.activity_data = ACTIVITY_STATIC[self.activity_id]

        self.activity_time = self.get_activity_time()

    def get_activity_time(self):
        def _find_start_time():
            start_time = self.activity_data.start_time
            if start_time:
                return start_time

            # 开服活动，初始时间由开服时间改成角色创建时间
            # 由于这是后加的，对于老玩家，还是按照开服时间算
            try:
                mc = MongoCharacter.objects.get(id=self.char_id)
            except DoesNotExist:
                return start_time

            if not mc.create_at:
                return start_time

            return arrow.get(mc.create_at).to(settings.TIME_ZONE)

        start_time = _find_start_time()

        return ActivityTime(
            start_time,
            self.activity_data.continued_days,
            self.activity_data.is_loop,
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
            # 周六 或 周日
            days = 7 - weekday
            new_start_time = t.init_date.replace(days=days)
            continued_days = 7
        else:
            new_start_time = t.init_date
            continued_days = 7 - weekday

        t = ActivityTime(
            new_start_time,
            continued_days,
            self.activity_data.is_loop,
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
        return [p.id]



@activities.register(5001)
class Activity5001(PurchaseCurrentValue, ActivityBase, ActivityTriggerMail):
    # 累计充值
    pass

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


@activities.register(12001)
class Activity12001(ActivityBase, ActivityTriggerAdditionalDrop):
    def get_additional_drop(self, stuff_id):
        if stuff_id != 33:
            return make_standard_drop_from_template()
        return ActivityTriggerAdditionalDrop.get_additional_drop(self)


    def get_current_value(self, char_id):
        return 0


@activities.register(13001)
class Activity13001(ActivityBase, ActivityTriggerAdditionalDrop):
    def get_current_value(self, char_id):
        return 0


@activities.register(14001)
class Activity14001(PurchaseCurrentValue, ActivityBase, ActivityTriggerMail):
    pass


@activities.register(15001)
class Activity15001(ActivityBase, ActivityTriggerAdditionalDrop):
    def get_current_value(self, char_id):
        return 0

    def get_additional_drop(self, stuff_id):
        if stuff_id != 33:
            return make_standard_drop_from_template()
        return ActivityTriggerAdditionalDrop.get_additional_drop(self)


# 16001, 17001 没有条件，只要达到就触发
# 这里特殊处理
@activities.register(16001)
class Activity16001(ActivityBase):
    # 充值给额外元宝
    def get_current_value(self, char_id):
        return 0

    def trig(self, extra_sycee):
        if not self.is_valid():
            return

        attachment = make_standard_drop_from_template()
        attachment['sycee'] = extra_sycee

        mail = Mail(self.char_id)
        mail.add(
            self.activity_data.mail_title,
            self.activity_data.mail_content,
            attachment=json.dumps(attachment)
        )



@activities.register(17001)
class Activity17001(ActivityBase):
    # 每天第一次任意额度的充值，给额外东西
    def get_current_value(self, char_id):
        now = arrow.utcnow().to(settings.TIME_ZONE)
        now_begin = arrow.Arrow(now.year, now.month, now.day).replace(tzinfo=now.tzinfo)
        condition = Q(char_id=self.char_id) & Q(purchase_at__gte=now_begin.timestamp) & Q(purchase_at__lte=now.timestamp)
        logs = MongoPurchaseLog.objects.filter(condition)

        value = 0
        for log in logs:
            value += log.sycee

        return value


    def trig(self, *args):
        if not self.is_valid():
            return

        now = arrow.utcnow().to(settings.TIME_ZONE)
        now_begin = arrow.Arrow(now.year, now.month, now.day).replace(tzinfo=now.tzinfo)

        condition = Q(char_id=self.char_id) & Q(purchase_at__gte=now_begin.timestamp) & Q(purchase_at__lte=now.timestamp)
        logs = MongoPurchaseLog.objects.filter(condition)
        if logs.count() == 0 or logs.count() > 1:
            # 没有充值，或者充值次数大于1,都返回
            # 只有当天第一次充值的时候，才给额外的东西
            return

        attachment = get_drop([self.activity_data.package])

        mail = Mail(self.char_id)
        mail.add(
            self.activity_data.mail_title,
            self.activity_data.mail_content,
            attachment=json.dumps(attachment)
        )


@activities.register(17002)
class Activity17002(PurchaseCurrentValue, ActivityBase):
    # 累计充值领月卡
    CONDITION_ID = -17002
    CONDITION_VALUE = 300

    def trig(self, *args):
        ac_record = ActivityConditionRecord(self.char_id, self.CONDITION_ID, self.activity_time)
        send_times = ac_record.send_times()

        value = self.get_current_value(self.char_id)
        times, _ = divmod(value, self.CONDITION_VALUE)
        if times <= send_times:
            return

        for i in range(times - send_times):
            p = BasePurchaseAction(self.char_id)
            p.send_reward_yueka(purchase_notify=False, as_vip_exp=False)

            m = Mail(self.char_id)
            m.add(
                "获得月卡",
                "您的累积充值已经达到了300元宝，获得了活动月卡奖励，300元宝的额外奖励已经放入您的帐号之中，请注意查收。从明天开始，接下来的30天，您将会每天获得100元宝。"
            )

        ac_record.add_send(times=times-send_times)



@activities.register(17003)
class Activity17003(ActivityBase):
    def get_current_value(self, char_id):
        return 0

    def trig(self, char_id):
        pass


@activities.register(999)
class Activity999(PurchaseCurrentValue, ActivityBase):
    CONDITION_ID = -999

    def trig(self, *args):
        ac_record = ActivityConditionRecord(self.char_id, self.CONDITION_ID, self.activity_time)
        send_times = ac_record.send_times()

        if send_times:
            return

        value = self.get_current_value(self.char_id)
        if not value:
            return

        attachment = get_drop([self.activity_data.package])

        mail = Mail(self.char_id)
        mail.add(
            self.activity_data.mail_title,
            self.activity_data.mail_content,
            attachment=json.dumps(attachment)
        )

        ac_record.add_send(1)

@activities.register(1000)
class Activity1000(ActivityBase):
    CONDITION_ID = -1000
    CONDITION_VALUE = 980

    def get_current_value(self, char_id):
        if not self.is_valid():
            return 0

        condition = Q(char_id=char_id) & Q(purchase_at__gte=self.activity_time.nearest_open_date.timestamp) & Q(purchase_at__lte=self.activity_time.nearest_close_date.timestamp)
        logs = MongoPurchaseLog.objects.filter(condition)

        sycee_list = [log.sycee for log in logs]
        if not sycee_list:
            return 0

        return max(sycee_list)


    def trig(self, *args):
        ac_record = ActivityConditionRecord(self.char_id, self.CONDITION_ID, self.activity_time)
        send_times = ac_record.send_times()

        if send_times:
            return

        value = self.get_current_value(self.char_id)
        if value < self.CONDITION_VALUE:
            return

        attachment = get_drop([self.activity_data.package])
        mail = Mail(self.char_id)
        mail.add(
            self.activity_data.mail_title,
            self.activity_data.mail_content,
            attachment=json.dumps(attachment)
        )

        ac_record.add_send(1)


@activities.register(18001)
class Activity18001(ActivityBase, ActivityTriggerManually):
    # 累计登录5天
    def get_current_value(self, char_id):
        if not self.is_valid():
            return 0

        return TimesLogLogin(char_id).days(
            start_at=self.activity_time.nearest_open_date.timestamp,
            end_at=self.activity_time.nearest_close_date.timestamp
        )

@activities.register(18002)
class Activity18002(ActivityBase, ActivityTriggerManually):
    # 装备进阶20次
    def get_current_value(self, char_id):
        if not self.is_valid():
            return 0

        return TimesLogEquipStepUp(char_id).count(
            start_at=self.activity_time.nearest_open_date.timestamp,
            end_at=self.activity_time.nearest_close_date.timestamp
        )

@activities.register(18004)
class Activity18004(ActivityBase, ActivityTriggerManually):
    # 武将进阶8次
    def get_current_value(self, char_id):
        if not self.is_valid():
            return 0

        return TimesLogHeroStepUp(char_id).count(
            start_at=self.activity_time.nearest_open_date.timestamp,
            end_at=self.activity_time.nearest_close_date.timestamp
        )

@activities.register(18005)
class Activity18005(ActivityBase, ActivityTriggerManually):
    # 精英副本通关50次
    def get_current_value(self, char_id):
        if not self.is_valid():
            return 0

        return TimesLogEliteStage(char_id).count(
            start_at=self.activity_time.nearest_open_date.timestamp,
            end_at=self.activity_time.nearest_close_date.timestamp
        )

@activities.register(18006)
class Activity18006(PurchaseCurrentValue, ActivityBase, ActivityTriggerManually):
    # 累计充值
    pass


@activities.register(18007)
class Activity18007(ActivityBase, ActivityTriggerManually):
    # 成功掠夺50次
    def get_current_value(self, char_id):
        if not self.is_valid():
            return 0

        return TimesLogPlunder(char_id).count(
            start_at=self.activity_time.nearest_open_date.timestamp,
            end_at=self.activity_time.nearest_close_date.timestamp
        )

@activities.register(18008)
class Activity18008(ActivityBase, ActivityTriggerManually):
    # 成功掠夺50次
    def get_current_value(self, char_id):
        if not self.is_valid():
            return 0

        return TimesLogGetHeroBySycee(char_id).count(
            start_at=self.activity_time.nearest_open_date.timestamp,
            end_at=self.activity_time.nearest_close_date.timestamp
        )

@activities.register(18009)
class Activity18009(ActivityBase, ActivityTriggerManually):
    # 累计武将挑战书 stuff_id = 3014
    STUFF_ID = 3014
    def get_current_value(self, char_id):
        from core.item import Item
        item = Item(char_id)
        return item.stuff_amount(self.STUFF_ID)

    def get_reward_check(self, char_id, condition_id):
        value = ACTIVITY_STATIC_CONDITIONS[condition_id].condition_value
        resource = Resource(char_id, "Activity Get Reward 18009")
        resource.check_and_remove(stuffs=[(self.STUFF_ID, value)])


@activities.register(19001)
class Activity19001(ActivityBase):
    CONDITION_ID = -19001
    CONDITION_VALUE = 198

    def get_current_value(self, char_id):
        ac_record = ActivityConditionRecord(self.char_id, self.CONDITION_ID, self.activity_time)
        return ac_record.send_times()

    def trig(self, *args):
        if not self.is_valid():
            return

        ac_record = ActivityConditionRecord(self.char_id, self.CONDITION_ID, self.activity_time)
        send_times = ac_record.send_times()

        if send_times >= 10:
            return


        condition = Q(char_id=self.char_id) & Q(purchase_at__gte=self.activity_time.nearest_open_date.timestamp) & Q(purchase_at__lte=self.activity_time.nearest_close_date.timestamp)
        logs = MongoPurchaseLog.objects.filter(condition)

        sycee_list = [log.sycee for log in logs if log.sycee >= self.CONDITION_VALUE]

        if len(sycee_list) > send_times:
            for i in range(len(sycee_list) - send_times):
                attachment = get_drop([self.activity_data.package])
                mail = Mail(self.char_id)
                mail.add(
                    self.activity_data.mail_title,
                    self.activity_data.mail_content,
                    attachment=json.dumps(attachment)
                )

                ac_record.add_send(1)


@activities.register(20001)
class Activity20001(PurchaseCurrentValue, ActivityBase, ActivityTriggerMail):
    pass


@activities.register(21001)
class Activity21001(ActivityBase):
    # 活动副本次数
    def get_current_value(self, char_id):
        return 0

    def get_max_times(self):
        if not self.is_valid():
            return ACTIVITY_STAGE_MAX_TIMES

        return ACTIVITY_STAGE_MAX_TIMES * 2

@activities.register(22001)
class Activity22001(ActivityBase):
    # VIP
    def get_current_value(self, char_id):
        return get_char_property(char_id, 'vip')

    def send_mail(self):
        attachment = get_drop([self.activity_data.package])
        mail = Mail(self.char_id)
        mail.add(
            self.activity_data.mail_title,
            self.activity_data.mail_content,
            attachment=json.dumps(attachment)
        )


# 组合活动
# 这个就是把活动A，B，C ... 完成了，再给个什么奖励
class CombineActivity(object):
    ACTIVITIES = []


# 活动类的统一入口
class ActivityEntry(object):
    def __new__(cls, char_id, activity_id):
        """

        :rtype : ActivityBase
        """
        return activities[activity_id](char_id)


class ActivityStatic(object):
    def __init__(self, char_id):
        self.char_id = char_id
        ActivityConditionRecord.fix(char_id)


    def trig(self, activity_id):
        entry = ActivityEntry(self.char_id, activity_id)
        if not entry.is_valid():
            return

        entry.trig(self.char_id)

        self.send_update_notify([activity_id])


    def get_reward(self, condition_id):
        activity_id = ACTIVITY_STATIC_CONDITIONS[condition_id].activity_id
        entry = ActivityEntry(self.char_id, activity_id)
        msg = entry.get_reward(self.char_id, condition_id)

        self.send_update_notify([activity_id])
        return msg


    def is_show(self, activity_id):
        # 是否显示
        entry = ActivityEntry(self.char_id, activity_id)
        return entry.is_valid()


    def _msg_activity(self, msg, activity_id):
        entry = ActivityEntry(self.char_id, activity_id)

        msg.id = activity_id
        msg.current_value = entry.get_current_value(self.char_id)
        msg.left_time = entry.left_time

        for i in entry.get_condition_ids():
            ac_record = ActivityConditionRecord(self.char_id, i, entry.activity_time)

            msg_condition = msg.conditions.add()
            msg_condition.id = i

            if entry.activity_data.mode == 1:
                if ac_record.in_reward():
                    status = ActivityEntryMsg.ActivityCondition.HAS_GOT
                elif entry.condition_is_passed(self.char_id, i):
                    status = ActivityEntryMsg.ActivityCondition.CAN_GET
                else:
                    status = ActivityEntryMsg.ActivityCondition.CAN_NOT
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


