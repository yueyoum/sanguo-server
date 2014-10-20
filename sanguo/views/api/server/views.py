# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-7-9'

from utils.decorate import json_return

from core.server import server
from core.version import version
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
        version_text = request.POST['version']
        index = int(request.POST['index'])
    except:
        return {'ret': 1}

    version.set_version(version_text)

    if index == 0:
        api_version_back(data={'version': version_text})
    return {'ret': 0}
