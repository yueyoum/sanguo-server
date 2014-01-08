# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/6/14'

from _base import Logger
from core.mongoscheme import MongoCheckIn


def reset():
    MongoCheckIn.objects.delete()
    logger = Logger('reset_checkin.log')
    logger.write("MongoCheckin Clean Done")
    logger.close()


if __name__ == '__main__':
    reset()
