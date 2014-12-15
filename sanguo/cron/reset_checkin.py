# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/6/14'

import uwsgidecorators

from cron.log import Logger
from core.mongoscheme import MongoCheckIn
from core.daily import CheckIn

# 每天0点清理签到

@uwsgidecorators.cron(0, 0, -1, -1, -1)
def reset(signum):
    for c in MongoCheckIn.objects.all():
        check = CheckIn(c.id)
        check.daily_reset()

    logger = Logger('reset_checkin.log')
    logger.write("MongoCheckin Daily Reset Done")
    logger.close()
