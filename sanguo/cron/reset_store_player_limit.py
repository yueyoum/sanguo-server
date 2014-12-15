# -*- coding: utf-8 -*-

import uwsgidecorators
from cron.log import Logger

from core.mongoscheme import MongoStoreCharLimit

@uwsgidecorators.cron(0, 0, -1, -1, -1)
def reset(signum):
    MongoStoreCharLimit.objects.delete()
    logger = Logger('reset_store_player_limit.log')
    logger.write("MongoStoreCharLimit Clean Done")
    logger.close()

