# -*- coding: utf-8 -*-

import os
import glob
import datetime

from cron.log import Logger

import uwsgidecorators

from django.conf import settings

# 每天0点清理战斗记录

DAYS_DIFF = 7

@uwsgidecorators.cron(0, 0, -1, -1, -1)
def clean(signum):
    now = datetime.datetime.now()
    DAY = now - datetime.timedelta(days=DAYS_DIFF)

    BATTLE_RECORD_PATH = settings.BATTLE_RECORD_PATH
    os.chdir(BATTLE_RECORD_PATH)
    amount = 0
    files = glob.glob('*.bin')
    for f in files:
        t = os.path.getctime(f)
        create_date = datetime.datetime.fromtimestamp(t)
        if create_date < DAY:
            os.unlink(f)
            amount += 1

    logger = Logger('clean_battle_record.log')
    logger.write("Clean Battle Record Done. Amount: {0}".format(amount))
    logger.close()


