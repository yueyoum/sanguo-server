# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '15-03-25'

import uwsgidecorators
from cron.log import Logger

from core.heropanel import HeroPanel

@uwsgidecorators.cron(0, 0, -1, -1, -1, target="spooler")
def reset(signum):
    logger = Logger("reset_hero_panel.log")
    HeroPanel.cron_job()

    logger.write("Rest Complete.")
    logger.close()
