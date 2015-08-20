# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/19/14'

import traceback
import uwsgidecorators
import arrow

from django.conf import settings

from cron.log import Logger
from core.mongoscheme import MongoCharacter
from core.plunder import Plunder


# 1点到8点之间不增加，其他时段每半小时增加一次
@uwsgidecorators.cron(-30, -1, -1, -1, -1, target="spooler")
def add_times(signum):
    hour = arrow.utcnow().to(settings.TIME_ZONE).hour
    if hour >= 1 and hour < 8:
        return

    logger = Logger('add_plunder_times.log')
    logger.write("Start")

    chars = MongoCharacter._get_collection().find({}, {'_id': 1})
    for char in chars:
        plunder = Plunder(char['_id'])
        try:
            plunder.change_current_plunder_times(change_value=1, allow_overflow=False)
        except:
            logger.error(traceback.format_exc())

    logger.write("add done")
    logger.close()


@uwsgidecorators.cron(0, 0, -1, -1, -1, target="spooler")
def reset_times(signum):
    logger = Logger("plunder_reset_times.log")
    logger.write("Start")

    try:
        Plunder.cron_job()
    except:
        logger.error(traceback.format_exc())
    else:
        logger.write("done")
    finally:
        logger.close()
