# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/20/14'

from _base import Logger
from core.mongoscheme import MongoTask

def reset():
    MongoTask.objects.delete()

    logger = Logger('reset_task.log')
    logger.write("MongoTask Clean Done")
    logger.close()

if __name__ == '__main__':
    reset()
