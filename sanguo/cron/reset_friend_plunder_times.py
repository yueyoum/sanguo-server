# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/6/14'

from _base import Logger
from core.mongoscheme import MongoFriend
from core.friend import Friend


def reset():
    logger = Logger('reset_friend_plunder_times.log')
    for f in MongoFriend.objects.all():
        friend = Friend(f.id)
        friend.daily_plunder_times_reset()

    logger.write("Friend Plunder Times Reset Done")
    logger.close()

if __name__ == '__main__':
    reset()
