# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/20/14'

import uwsgidecorators

from cron.log import Logger
from core.attachment import Attachment


@uwsgidecorators.cron(0, 0, -1, -1, -1)
def reset(signum):
    logger = Logger('reset_prize.log')
    Attachment.cron_job()

    logger.write("Attachment Prize Reset Done")
    logger.close()
