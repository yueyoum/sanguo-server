# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-9'

import json
from django.conf import settings

from utils.api import APIFailure, apicall

TIMER_REGISTER = settings.TIMER_REGISTER
TIMER_UNREGISTER = settings.TIMER_UNREGISTER
TIMER_CALLBACK = settings.TIMER_CALLBACK



def register(data, seconds):
    req_data = {
        'callback_cmd': TIMER_CALLBACK,
        'callback_data': json.dumps(data),
        'seconds': seconds
    }

    req = apicall(data=json.dumps(req_data), cmd=TIMER_REGISTER)
    return req['data']['key']


def unregister(key):
    req_data = {
        'key': key
    }

    req = apicall(data=json.dumps(req_data), cmd=TIMER_UNREGISTER)
    return req['data']['ttl']
