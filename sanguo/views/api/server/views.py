# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-7-9'

from django.conf import settings
from utils.decorate import json_return

from core.server import server
from utils.api import api_version_back

@json_return
def feedback(request):
    try:
        status = int(request.POST['status'])
    except:
        return {'ret': 1}

    active = status != 4
    server.active = active
    return {'ret': 0}

@json_return
def version_change(request):
    try:
        version = request.POST['version']
        index = int(request.POST['index'])
    except:
        return {'ret': 1}

    settings.SERVER_VERSION = version

    if index == 0:
        api_version_back(data={'version': version})
    return {'ret': 0}
