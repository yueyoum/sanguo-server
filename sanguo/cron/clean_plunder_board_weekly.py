# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/27/14'

from _base import Logger

from core.plunder import PlunderLeaderboardWeekly

def clean():
    logger = Logger("clean_plunder_board_weekly.log")
    PlunderLeaderboardWeekly.clean()
    logger.write("Clean Complete.")
    logger.close()

if __name__ == '__main__':
    clean()

