# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/20/14'

import uwsgidecorators

from cron.log import Logger
from core.mongoscheme import MongoAttachment


NEED_RESET_PRIZE_IDS = [4, 5]

@uwsgidecorators.cron(0, 0, -1, -1, -1)
def reset(signum):
    logger = Logger('reset_prize.log')

    for att in MongoAttachment.objects.all():
        _changed = False
        for _rst in NEED_RESET_PRIZE_IDS:
            if _rst in att.prize_ids:
                att.prize_ids.remove(_rst)
                _changed = True

        if _changed:
            att.save()

    logger.write("Attachment Prize Reset Done")
    logger.close()
