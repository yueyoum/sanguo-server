# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/27/14'

import traceback

import uwsgidecorators

from cron.log import Logger
from core.activeplayers import ActivePlayers


@uwsgidecorators.timer(300, target="mule")
def clean(signum):
    logger = Logger("clean_active_players.log")
    logger.write("Start.")

    try:
        result = ActivePlayers().clean()
    except:
        logger.error(traceback.format_exc())
    else:
        logger.write("Complete. {0}".format(result))
    finally:
        logger.close()
