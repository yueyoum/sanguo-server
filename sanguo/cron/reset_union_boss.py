# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-12-15'

import uwsgidecorators
from cron.log import Logger

from core.mongoscheme import MongoUnionBoss

@uwsgidecorators.cron(0, 0, -1, -1, -1)
def reset(signum):
    logger = Logger("reset_union_boss.log")
    logger.write("Start.")

    for mb in MongoUnionBoss.objects.all():
        mb.opened = {}
        mb.save()

    logger.write("Complete.")