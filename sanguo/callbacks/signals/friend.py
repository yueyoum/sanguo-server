# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-8-14'

from core.signals import new_friend_got_signal
from core.achievement import Achievement

def _new_friend_got(char_id, new_friend_id, total_friends_amount, **kwargs):
    achievement = Achievement(char_id)
    achievement.trig(27, total_friends_amount)


new_friend_got_signal.connect(
    _new_friend_got,
    dispatch_uid='callbacks.signals.friend._new_friend_got'
)

