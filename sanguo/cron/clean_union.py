# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '12/09/14'

import uwsgidecorators

from cron.log import Logger

from core.union.battle import UnionBattle
from core.union.member import Member

# 每天0点清理
@uwsgidecorators.cron(0, 0, -1, -1, -1)
def clean(signum):
    logger = Logger("clean_union.log")

    UnionBattle.cron_job()
    Member.cron_job()

    logger.write("Clean Union Complete.")
    logger.close()
