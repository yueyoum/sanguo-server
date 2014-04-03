# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/3/14'

from functools import partial

import requests

from django.conf import settings

GATE_URL = settings.GATE_URL

def apicall(data, cmd):
    x = requests.post('{0}{1}'.format(GATE_URL, cmd), data)
    return x.json()


api_server_report = partial(apicall, cmd='/api/server-list/report/')
api_account_login = partial(apicall, cmd='/api/account/login/')
api_character_create = partial(apicall, cmd='/api/character/create/')

