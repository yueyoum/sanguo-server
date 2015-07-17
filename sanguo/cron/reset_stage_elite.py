# -*- coding:utf-8 -*-

import uwsgidecorators
from cron.log import Logger

from core.mongoscheme import MongoStage

@uwsgidecorators.cron(0, 0, -1, -1, -1, target="spooler")
def reset(signum):
    logger = Logger('reset_stage_elite.log')
    logger.write("Reset Stage Elite Times Start")
    for ms in MongoStage.objects.filter(elite_changed=True):
        for k in ms.elites.keys():
            ms.elites[k] = 0

        ms.elites_buy = {}
        ms.elite_changed = False
        ms.save()

    logger.write("Done")
    logger.close()
