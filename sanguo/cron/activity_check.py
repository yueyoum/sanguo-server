# -*- coding: utf-8 -*-
"""
Author:         Wang Chao <yueyoum@gmail.com>
Filename:       activity_check.py
Date Created:   2015-06-24 16:59
Description:

"""

import uwsgidecorators
import arrow
from core.mongoscheme import MongoPurchaseLog

from cron.log import Logger
from core.activity import ActivityEntry

@uwsgidecorators.cron(0, 0, -1, -1, -1)
def purchase_check(signum):
    logger = Logger("purchase_check.log")
    logger.write("Start")

    amount = 0
    last_day = arrow.utcnow().replace(days=-1)
    logs = MongoPurchaseLog.objects.filter(purchase_at__gte=last_day.timestamp).distinct("char_id")
    for char_id in logs:
        ActivityEntry(char_id, 17001)
        amount += 1

    logger.write("Done. Process Amount: {0}".format(amount))
    logger.close()

