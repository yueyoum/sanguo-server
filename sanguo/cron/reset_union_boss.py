# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-12-15'

import uwsgidecorators
from cron.log import Logger

from core.mongoscheme import MongoUnionBoss

@uwsgidecorators.cron(0, 0, -1, -1, -1, target="worker")
def reset(signum):
    logger = Logger("reset_union_boss.log")
    MongoUnionBoss.drop_collection()

    logger.write("Rest Complete.")
    logger.close()

