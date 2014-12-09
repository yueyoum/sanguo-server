# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '12/09/14'

from _base import Logger

from core.union import UnionBattle, UnionMember
from core.mongoscheme import MongoUnion, MongoUnionMember

def clean():
    logger = Logger("clean_union.log")
    for x in MongoUnion.objects.all():
        UnionBattle(x.owner).cron_job()

    for x in MongoUnionMember.objects.all():
        UnionMember(x.id).cron_job()

    logger.write("Clean Union Complete.")
    logger.close()


if __name__ == '__main__':
    clean()

