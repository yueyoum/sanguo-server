# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '12/09/14'

import traceback

import uwsgidecorators

from cron.log import Logger

from core.union.battle import UnionBattle
from core.union.member import Member

# 每天0点清理
@uwsgidecorators.cron(0, 0, -1, -1, -1, target="spooler")
def clean(signum):
    logger = Logger("clean_union.log")
    logger.write("Start")

    try:
        UnionBattle.cron_job()
        Member.cron_job()
    except:
        logger.error(traceback.format_exc())
    else:
        logger.write("Clean Union Complete.")
    finally:
        logger.close()
