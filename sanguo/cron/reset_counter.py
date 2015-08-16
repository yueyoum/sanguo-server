# -*- coding: utf-8 -*-

import uwsgidecorators
import traceback

from cron.log import Logger

from core.mongoscheme import MongoCounter

# 每天0点清理次数

@uwsgidecorators.cron(0, 0, -1, -1 ,-1, target="spooler")
def reset(signum):
    logger = Logger('reset_counter.log')
    logger.write("Start")
    try:
        MongoCounter.objects.delete()
    except:
        logger.error(traceback.format_exc())
    else:
        logger.write("Done")
    finally:
        logger.close()
