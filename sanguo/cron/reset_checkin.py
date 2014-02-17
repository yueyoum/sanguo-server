# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/6/14'

from _base import Logger
from core.mongoscheme import MongoCheckIn
from core.daily import CheckIn


def reset():
    for c in MongoCheckIn.objects.all():
        check = CheckIn(c.id)
        check.daily_reset()

    logger = Logger('reset_checkin.log')
    logger.write("MongoCheckin Daily Reset Done")
    logger.close()

if __name__ == '__main__':
    reset()
