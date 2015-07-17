# -*- coding: utf-8 -*-

import uwsgidecorators

from cron.log import Logger

from core.mongoscheme import MongoCounter

# 每天0点清理次数

@uwsgidecorators.cron(0, 0, -1, -1 ,-1, target="spooler")
def reset(signum):
    MongoCounter.objects.delete()
    logger = Logger('reset_counter.log')
    logger.write("MongoCounter Clean Done")
    logger.close()
