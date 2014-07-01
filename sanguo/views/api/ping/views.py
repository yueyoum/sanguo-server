# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-7-1'

from utils.decorate import json_return
from core.activeplayers import ActivePlayers
from preset.settings import SERVER_STATUS

@json_return
def ping(request):
    ap = ActivePlayers()
    amount = ap.amount

    status = None
    for n, s in SERVER_STATUS:
        if amount >= n:
            status = s
            break

    if not status:
        status = 1

    return {
        'ret': 0,
        'data': {
            'status': status
        }
    }
