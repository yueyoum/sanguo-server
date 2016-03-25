# -*- coding: utf-8 -*-
"""
Author:         Wang Chao <yueyoum@gmail.com>
Filename:       times_log
Date Created:   2016-02-26 14-02
Description:

"""
import uuid
import arrow

from mongoengine import Q

from django.conf import settings
from core.mongoscheme import MongoTimesLog
from core.activity import has_activity

class TimesLog(object):
    KEY = None
    ACTIVITY_ID = None

    def __init__(self, char_id):
        self.char_id = char_id
        self.key = "{0}:{1}".format(self.KEY, char_id)

    def inc(self):
        from core.activity import ActivityStatic

        log = MongoTimesLog(id=str(uuid.uuid4()))
        log.key = self.key
        log.timestamp = arrow.utcnow().timestamp
        log.save()

        if self.ACTIVITY_ID and has_activity(self.ACTIVITY_ID):
            ActivityStatic(self.char_id).trig(self.ACTIVITY_ID)

    def count(self, start_at=None, end_at=None):
        condition = Q(key=self.key)
        if start_at:
            condition &= Q(timestamp__gte=start_at)
        if end_at:
            condition &= Q(timestamp__lte=end_at)

        return MongoTimesLog.objects.filter(condition).count()

    def days(self, start_at, end_at):
        condition = Q(key=self.key) & Q(timestamp__gte=start_at) & Q(timestamp__lte=end_at)
        dates = set()
        for log in MongoTimesLog.objects.filter(condition):
            date = arrow.get(log.timestamp).to(settings.TIME_ZONE).format("YYYY-MM-DD")
            dates.add(date)

        return len(dates)

#登录次数
class TimesLogLogin(TimesLog):
    KEY = 'login'
    ACTIVITY_ID = 18001

#装备进阶
class TimesLogEquipStepUp(TimesLog):
    KEY = 'equip_step_up'
    ACTIVITY_ID = 18002

#武将进阶
class TimesLogHeroStepUp(TimesLog):
    KEY = 'hero_step_up'
    ACTIVITY_ID = 18004

#精英关卡
class TimesLogEliteStage(TimesLog):
    KEY = 'elite_stage'
    ACTIVITY_ID = 18005

#掠夺次数
class TimesLogPlunder(TimesLog):
    KEY = 'plunder'
    ACTIVITY_ID = 18007

#元宝点将
class TimesLogGetHeroBySycee(TimesLog):
    KEY = 'get_hero_sycee'
    ACTIVITY_ID = 18008

#竞技场比武
class TimesLogArena(TimesLog):
    KEY = 'arena'
    ACTIVITY_ID = 30001

#宝石合成
class TimesLogGemMerge(TimesLog):
    KEY = 'gem_merge'
    ACTIVITY_ID = 30002