# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/27/14'


from _base import Logger

from core.activeplayers import ActivePlayers

def clean():
    logger = Logger("clean_active_players.log")
    logger.write("Start.")

    result = ActivePlayers.clean_all()

    logger.write("Complete. {0}".format(result))
    logger.close()

if __name__ == '__main__':
    clean()
