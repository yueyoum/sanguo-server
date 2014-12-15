# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '12/09/14'

import uwsgidecorators

from cron.log import Logger

from core.union.battle import UnionBattle
from core.union.member import Member
from core.mongoscheme import MongoUnion, MongoUnionMember

# 每天0点清理
@uwsgidecorators.cron(0, 0, -1, -1, -1)
def clean(signum):
    logger = Logger("clean_union.log")
    for x in MongoUnion.objects.all():
        UnionBattle(x.owner).cron_job()

    for x in MongoUnionMember.objects.all():
        Member(x.id).cron_job()

    logger.write("Clean Union Complete.")
    logger.close()
