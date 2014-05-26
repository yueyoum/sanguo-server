# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/3/14'

from functools import partial

import requests

from django.conf import settings

HUB_URL = "http://{0}:{1}".format(settings.HUB_HOST, settings.HUB_PORT)

def apicall(data, cmd):
    x = requests.post('{0}{1}'.format(HUB_URL, cmd), data)
    return x.json()


api_server_report = partial(apicall, cmd='/api/server-list/report/')
api_account_login = partial(apicall, cmd='/api/account/login/')
api_account_bind = partial(apicall, cmd='/api/account/bind/')
api_character_create = partial(apicall, cmd='/api/character/create/')

api_store_get = partial(apicall, cmd='/api/store/get/')
api_store_buy = partial(apicall, cmd='/api/store/buy/')

api_activatecode_use = partial(apicall, cmd='/api/activatecode/use/')
