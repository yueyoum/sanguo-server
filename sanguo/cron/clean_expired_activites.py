# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '15-2-9'

import uwsgidecorators

from cron.log import Logger

from core.mongoscheme import MongoActivityStatic
from core.activity import ActivityEntry
from preset.data import ACTIVITY_STATIC


# 每天零点清理过期活动
@uwsgidecorators.cron(0, 0, -1, -1, -1)
def clean_expired_activity(signum):
    logger = Logger("clean_expired_activity.log")
    for mongo_ac in MongoActivityStatic.objects.all():
        for aid in ACTIVITY_STATIC.keys():
            entry = ActivityEntry(aid)
            if entry.activity_data.category == 1:
                # 开服活动
                continue

            if entry.is_valid():
                continue

            # 过期的常规活动，删除记录
            condition_ids = entry.get_condition_ids()
            for cid in condition_ids:
                if str(cid) in mongo_ac.reward_times:
                    mongo_ac.reward_times.pop(str(cid))
                if str(cid) in mongo_ac.send_times:
                    mongo_ac.send_times.pop(str(cid))

        mongo_ac.save()

    logger.write("clean expired activity done")
    logger.close()
