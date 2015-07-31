# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/20/14'

import uwsgidecorators
from cron.log import Logger
from core.mongoscheme import MongoTask

@uwsgidecorators.cron(0, 0, -1, -1, -1, target="mule")
def reset(signum):
    MongoTask.objects.delete()

    logger = Logger('reset_task.log')
    logger.write("MongoTask Clean Done")
    logger.close()
