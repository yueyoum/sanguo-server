# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/3/14'

from functools import partial
from django.conf import settings

from libs.apiclient import APIFailure, HTTPAPIClient, HTTPSAPIClient

HUB_URL = "http://{0}:{1}".format(settings.HUB_HOST, settings.HUB_PORT)

HTTPSAPIClient.install_pem('/opt/ca/client.pem')
apicall = HTTPSAPIClient()


api_server_report = partial(apicall, cmd=HUB_URL + '/api/server-list/report/')
api_account_login = partial(apicall, cmd=HUB_URL + '/api/account/login/')
api_account_bind = partial(apicall, cmd=HUB_URL + '/api/account/bind/')
api_character_create = partial(apicall, cmd=HUB_URL + '/api/character/create/')

api_store_get = partial(apicall, cmd=HUB_URL + '/api/store/get/')
api_store_buy = partial(apicall, cmd=HUB_URL + '/api/store/buy/')

api_activatecode_use = partial(apicall, cmd=HUB_URL + '/api/activatecode/use/')
