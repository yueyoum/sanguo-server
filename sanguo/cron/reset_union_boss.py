# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-12-15'

import traceback

import uwsgidecorators
from cron.log import Logger

from core.mongoscheme import MongoUnionBoss

@uwsgidecorators.cron(0, 0, -1, -1, -1, target="spooler")
def reset(signum):
    logger = Logger("reset_union_boss.log")
    logger.write("Start")

    try:
        MongoUnionBoss.drop_collection()
    except:
        logger.error(traceback.format_exc())
    else:
        logger.write("Rest Complete.")
    finally:
        logger.close()

