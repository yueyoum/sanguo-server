# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/20/14'

import traceback
import uwsgidecorators

from cron.log import Logger
from core.attachment import Attachment


@uwsgidecorators.cron(0, 0, -1, -1, -1, target="mule")
def reset(signum):
    logger = Logger('reset_prize.log')
    logger.write("Start")

    try:
        Attachment.cron_job()
    except:
        logger.error(traceback.format_exc())
    else:
        logger.write("Done")
    finally:
        logger.close()
