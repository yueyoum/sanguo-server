# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/6/14'

import traceback

import uwsgidecorators

from cron.log import Logger
from core.friend import Friend

# 每天0点清理好友赠送掠夺次数

@uwsgidecorators.cron(0, 0, -1, -1, -1, target="mule")
def reset(signum):
    logger = Logger('reset_friend_plunder_times.log')
    logger.write("Start")

    try:
        Friend.cron_job()
    except:
        logger.error(traceback.format_exc())
    else:
        logger.write("Done")
    finally:
        logger.close()

