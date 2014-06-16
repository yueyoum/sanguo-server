# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-9'

import json
from django.conf import settings

from core.server import SERVERS

from utils.api import apicall

TIMER_REGISTER = settings.TIMER_REGISTER
TIMER_UNREGISTER = settings.TIMER_UNREGISTER

SELF_HTTPS_URL = 'https://{0}:{1}'.format(SERVERS.values()[0]['host']['port_https'])
CALLBACK_HANG_URL = SELF_HTTPS_URL + '/api/timer/hang/'


def register(data, seconds):
    req_data = {
        'callback_cmd': CALLBACK_HANG_URL,
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
