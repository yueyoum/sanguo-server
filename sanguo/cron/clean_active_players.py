# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/27/14'


from _base import Logger

from core.activeplayers import ActivePlayers

def clean():
    logger = Logger("clean_active_players.log")
    logger.write("Start.")

    amount = ActivePlayers.clean_all()

    logger.write("Complete. Cleaned Amount: {0}".format(amount))
    logger.close()

if __name__ == '__main__':
    clean()

