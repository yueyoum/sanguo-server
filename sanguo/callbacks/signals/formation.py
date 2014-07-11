# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-7-11'

from core.signals import socket_hero_changed_signal
from core.character import Char

def _socket_hero_changed(char_id, socket_id, hero_id, **kwargs):
    if socket_id == 1:
        char = Char(char_id)
        char.send_notify()

socket_hero_changed_signal.connect(
    _socket_hero_changed,
    dispatch_uid='callbacks.signals.formation._socket_hero_changed'
)
