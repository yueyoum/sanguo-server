# -*- coding: utf-8 -*-

import traceback

import uwsgidecorators
from cron.log import Logger

from core.mongoscheme import MongoStoreCharLimit

@uwsgidecorators.cron(0, 0, -1, -1, -1, target="mule")
def reset(signum):
    logger = Logger('reset_store_player_limit.log')
    logger.write("Start")

    try:
        MongoStoreCharLimit.objects.delete()
    except:
        logger.error(traceback.format_exc())
    else:
        logger.write("MongoStoreCharLimit Clean Done")
    finally:
        logger.close()

