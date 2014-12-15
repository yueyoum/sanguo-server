# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/27/14'

import uwsgidecorators

from cron.log import Logger
from core.activeplayers import ActivePlayers

# 每办小时清理在线用户

@uwsgidecorators.cron(-30, -1, -1, -1, -1)
def clean(signum):
    logger = Logger("clean_active_players.log")
    logger.write("Start.")

    result = ActivePlayers().clean()

    logger.write("Complete. {0}".format(result))
    logger.close()
