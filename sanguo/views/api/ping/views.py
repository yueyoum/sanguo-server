# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-7-1'

from utils.decorate import json_return
from core.activeplayers import ActivePlayers

@json_return
def ping(request):
    ap = ActivePlayers()
    amount = ap.amount

    return {
        'ret': 0,
        'data': {
            'active_amount': amount,
        }
    }
