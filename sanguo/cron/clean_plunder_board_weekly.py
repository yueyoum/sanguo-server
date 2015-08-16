# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/27/14'

import traceback

import uwsgidecorators

from cron.log import Logger

from core.plunder import PlunderLeaderboardWeekly


# 每周清理掠夺榜单

@uwsgidecorators.cron(0, 0, -1, -1, 1, target="spooler")
def clean(signum):
    logger = Logger("clean_plunder_board_weekly.log")
    logger.write("Start")

    try:
        PlunderLeaderboardWeekly.clean()
    except:
        logger.error(traceback.format_exc())
    else:
        logger.write("Done")
    finally:
        logger.close()
