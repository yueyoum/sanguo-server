# -*- coding:utf-8 -*-

import uwsgidecorators
from cron.log import Logger

from core.mongoscheme import MongoStage

@uwsgidecorators.cron(0, 0, -1, -1, -1)
def reset(signum):
    logger = Logger('reset_stage_elite.log')
    logger.write("Reset Stage Elite Times Start")
    for ms in MongoStage.objects.all():
        for k in ms.elites.keys():
            ms.elites[k] = 0

        for k in ms.elites_buy.keys():
            ms.elites_buy[k] = 0

        ms.elites_buy = {}
        ms.save()

    logger.write("Done")
    logger.close()
