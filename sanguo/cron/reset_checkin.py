# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/6/14'

import uwsgidecorators

from cron.log import Logger
from core.daily import CheckIn

# 每天0点清理签到

@uwsgidecorators.cron(0, 0, -1, -1, -1, target="mule")
def reset(signum):
    CheckIn.cron_job()

    logger = Logger('reset_checkin.log')
    logger.write("MongoCheckin Daily Reset Done")
    logger.close()
